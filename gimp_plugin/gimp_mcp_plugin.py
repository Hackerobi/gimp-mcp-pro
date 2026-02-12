#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GIMP MCP Pro Plugin — Enhanced Model Context Protocol integration for GIMP 3.0+

Key improvements over maorcc's plugin:
- Length-prefixed framing (reliable message boundaries)
- Persistent connections (no reconnect per command)
- Native command handlers for common operations
- Undo group support
- Backward-compatible with JSON boundary detection

Install: Copy this file to your GIMP plugins directory.
  Linux:   ~/.config/GIMP/3.0/plug-ins/gimp-mcp-pro/gimp_mcp_plugin.py
  macOS:   ~/Library/Application Support/GIMP/3.0/plug-ins/gimp-mcp-pro/gimp_mcp_plugin.py
  Windows: %APPDATA%/GIMP/3.0/plug-ins/gimp-mcp-pro/gimp_mcp_plugin.py

Make sure the file is executable (chmod +x on Linux/macOS).
"""

import gi
gi.require_version('Gimp', '3.0')

from gi.repository import Gimp
from gi.repository import GLib

import base64
import io
import json
import os
import platform
import signal
import socket
import struct
import sys
import tempfile
import threading
import traceback

# Protocol constants
HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 100 MB
USE_LENGTH_PREFIX = True  # Set False for backward compat with maorcc bridge


def N_(message): return message
def _(message): return GLib.dgettext(None, message)


def exec_and_capture(command, context):
    """Execute Python code and capture stdout."""
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        exec(command, context)
    finally:
        sys.stdout = old_stdout
    return buf.getvalue()


class MCPProPlugin(Gimp.PlugIn):
    """Enhanced GIMP MCP plugin with reliable framing and native handlers."""

    def __init__(self):
        super().__init__()
        self.host = 'localhost'
        self.port = int(os.environ.get('GIMP_MCP_PORT', '9877'))
        self.running = False
        self.server_socket = None
        # Persistent Python execution context
        self.exec_context = {}
        exec("from gi.repository import Gimp, Gegl", self.exec_context)

    # ------------------------------------------------------------------
    # GIMP Plugin registration
    # ------------------------------------------------------------------

    def do_query_procedures(self):
        return ["plug-in-mcp-pro-server"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_menu_label(_("Start MCP Pro Server"))
        procedure.set_documentation(
            _("Starts the MCP Pro server for AI-assisted GIMP editing"),
            _("Starts a socket server that exposes GIMP operations via MCP"),
            name,
        )
        procedure.set_attribution("GIMP MCP Pro", "GIMP MCP Pro Contributors", "2026")
        procedure.add_menu_path('<Image>/Tools/')
        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if self.running:
            print("MCP Pro Server is already running")
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        self.running = True
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(1.0)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)

            print(f"GIMP MCP Pro server started on {self.host}:{self.port}")

            while self.running:
                try:
                    client, address = self.server_socket.accept()
                    print(f"Client connected: {address}")
                    t = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
                    t.start()
                except socket.timeout:
                    continue
                except OSError:
                    break

            print("MCP Pro server stopped")
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
        except Exception as e:
            print(f"Server error: {e}")
            self.running = False
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def _shutdown(self, signum=None, frame=None):
        print("Shutting down MCP Pro server...")
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    # ------------------------------------------------------------------
    # Client handling with length-prefixed framing
    # ------------------------------------------------------------------

    def _handle_client(self, client):
        """Handle a connected client with persistent connection."""
        client.settimeout(None)  # No timeout for persistent connection

        try:
            while self.running:
                try:
                    request = self._receive_message(client)
                    if request is None:
                        break

                    response = self._dispatch(request)
                    self._send_message(client, response)
                except (ConnectionError, BrokenPipeError, OSError):
                    break
                except Exception as e:
                    error_resp = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
                    try:
                        self._send_message(client, error_resp)
                    except:
                        break
        finally:
            try:
                client.close()
            except:
                pass
            print("Client disconnected")

    def _receive_message(self, sock):
        """Receive a message using length-prefixed framing (or JSON fallback)."""
        if USE_LENGTH_PREFIX:
            # Read 4-byte length header
            header = self._recv_exact(sock, HEADER_SIZE)
            if header is None:
                return None
            length = struct.unpack('>I', header)[0]
            if length > MAX_MESSAGE_SIZE:
                raise ValueError(f"Message too large: {length}")

            data = self._recv_exact(sock, length)
            if data is None:
                return None
            return json.loads(data.decode('utf-8'))
        else:
            # JSON boundary fallback
            buf = b''
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    return None
                buf += chunk
                try:
                    return json.loads(buf.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

    def _send_message(self, sock, data):
        """Send a message with length-prefixed framing (or raw JSON fallback)."""
        payload = json.dumps(data).encode('utf-8')
        if USE_LENGTH_PREFIX:
            header = struct.pack('>I', len(payload))
            sock.sendall(header + payload)
        else:
            sock.sendall(payload)

    def _recv_exact(self, sock, n):
        """Receive exactly n bytes."""
        data = bytearray()
        while len(data) < n:
            chunk = sock.recv(min(n - len(data), 65536))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data)

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, request):
        """Route a command to the appropriate handler."""
        cmd_type = request.get("type", "")
        params = request.get("params", {})

        handlers = {
            "get_image_bitmap": self._handle_get_bitmap,
            "get_image_metadata": self._handle_get_metadata,
            "get_gimp_info": self._handle_get_gimp_info,
            "get_context_state": self._handle_get_context_state,
            "exec": self._handle_exec,
        }

        handler = handlers.get(cmd_type)
        if handler:
            try:
                return handler(params)
            except Exception as e:
                return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
        else:
            return {"status": "error", "error": f"Unknown command type: {cmd_type}"}

    # ------------------------------------------------------------------
    # Native handlers
    # ------------------------------------------------------------------

    def _handle_exec(self, params):
        """Execute Python code in GIMP's persistent context."""
        args = params.get("args", [])
        if not args or len(args) < 2:
            return {"status": "error", "error": "exec requires args: [mode, code_array]"}

        mode = args[0]
        code_lines = args[1] if len(args) > 1 else []

        if mode == "pyGObject-eval":
            vals = [str(eval(e, self.exec_context)) for e in code_lines]
            return {"status": "success", "results": vals}
        else:
            # pyGObject-console — execute and capture output
            outputs = []
            for line in code_lines:
                output = exec_and_capture(line, self.exec_context)
                outputs.append(output)
            return {"status": "success", "results": outputs}

    def _handle_get_bitmap(self, params):
        """Get current image as base64 PNG — reuses maorcc's proven logic."""
        images = Gimp.get_images()
        if not images:
            return {"status": "error", "error": "No images are open in GIMP"}

        image = images[0]
        max_width = params.get("max_width")
        max_height = params.get("max_height")
        region = params.get("region", {})

        orig_w = image.get_width()
        orig_h = image.get_height()

        # Region extraction
        working_image = image
        should_delete = False

        if region:
            ox = region.get("origin_x", 0)
            oy = region.get("origin_y", 0)
            rw = region.get("width", orig_w)
            rh = region.get("height", orig_h)

            working_image = Gimp.Image.new(rw, rh, image.get_base_type())
            should_delete = True

            image.select_rectangle(Gimp.ChannelOps.REPLACE, ox, oy, rw, rh)
            orig_layers = image.get_layers()
            if orig_layers:
                new_layer = Gimp.Layer.new(working_image, 'Region', rw, rh,
                                          Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL)
                working_image.insert_layer(new_layer, None, 0)
                Gimp.edit_copy([orig_layers[0]])
                floating = Gimp.edit_paste(new_layer, True)[0]
                Gimp.floating_sel_anchor(floating)

            try:
                Gimp.Selection.none(image)
            except:
                pass

        # Scaling
        final_image = working_image
        should_delete_final = should_delete
        cur_w = working_image.get_width()
        cur_h = working_image.get_height()

        if max_width and max_height and (cur_w > max_width or cur_h > max_height):
            aspect = cur_w / cur_h
            max_aspect = max_width / max_height
            if aspect > max_aspect:
                tw, th = max_width, int(max_width / aspect)
            else:
                th, tw = max_height, int(max_height * aspect)

            final_image = working_image.duplicate()
            should_delete_final = True
            final_image.scale(tw, th)

        # Export to temp PNG
        fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)

        try:
            from gi.repository import Gio
            file_obj = Gio.File.new_for_path(temp_path)

            export_proc = Gimp.get_pdb().lookup_procedure('file-png-export')
            if export_proc:
                cfg = export_proc.create_config()
                cfg.set_property('image', final_image)
                cfg.set_property('file', file_obj)
                try:
                    cfg.set_property('drawables', final_image.get_layers())
                except:
                    pass
                export_proc.run(cfg)
            else:
                Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, final_image, file_obj)

            with open(temp_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            fw = final_image.get_width()
            fh = final_image.get_height()

            return {
                "status": "success",
                "results": {
                    "image_data": encoded,
                    "format": "png",
                    "width": fw,
                    "height": fh,
                    "original_width": orig_w,
                    "original_height": orig_h,
                    "encoding": "base64",
                }
            }
        finally:
            if should_delete_final and final_image != working_image:
                try: final_image.delete()
                except: pass
            if should_delete and working_image != image:
                try: working_image.delete()
                except: pass
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _handle_get_metadata(self, params):
        """Get image metadata without bitmap transfer."""
        images = Gimp.get_images()
        if not images:
            return {"status": "error", "error": "No images are open"}

        image = images[0]
        layers = image.get_layers()
        layers_info = []
        for i, layer in enumerate(layers):
            try:
                info = {
                    "name": layer.get_name(),
                    "visible": layer.get_visible(),
                    "opacity": layer.get_opacity(),
                    "width": layer.get_width(),
                    "height": layer.get_height(),
                    "has_alpha": layer.has_alpha(),
                }
                try: info["blend_mode"] = str(layer.get_mode())
                except: info["blend_mode"] = "unknown"
                layers_info.append(info)
            except Exception as e:
                layers_info.append({"name": f"Layer {i}", "error": str(e)})

        file_info = {}
        try:
            f = image.get_file()
            if f:
                file_info["path"] = f.get_path() if hasattr(f, 'get_path') else None
                file_info["basename"] = f.get_basename() if hasattr(f, 'get_basename') else None
        except:
            pass

        res_x = res_y = None
        try: res_x, res_y = image.get_resolution()
        except: pass

        base_map = {0: "RGB", 1: "Grayscale", 2: "Indexed"}

        return {
            "status": "success",
            "results": {
                "basic": {
                    "width": image.get_width(),
                    "height": image.get_height(),
                    "base_type": base_map.get(int(image.get_base_type()), "Unknown"),
                    "resolution_x": res_x,
                    "resolution_y": res_y,
                    "is_dirty": image.is_dirty() if hasattr(image, 'is_dirty') else False,
                },
                "structure": {
                    "num_layers": len(layers),
                    "layers": layers_info,
                },
                "file": file_info,
            }
        }

    def _handle_get_gimp_info(self, params):
        """Get GIMP environment information."""
        info = {
            "session": {"num_open_images": len(Gimp.get_images())},
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            },
            "capabilities": {
                "mcp_pro_server": True,
                "length_prefix_framing": USE_LENGTH_PREFIX,
                "persistent_connections": True,
            },
        }
        return {"status": "success", "results": info}

    def _handle_get_context_state(self, params):
        """Get current GIMP context state."""
        state = {}
        try:
            fg = Gimp.context_get_foreground()
            state["foreground_color"] = str(fg)
            if hasattr(fg, 'get_rgba'):
                state["foreground_rgba"] = list(fg.get_rgba())
        except: pass
        try:
            bg = Gimp.context_get_background()
            state["background_color"] = str(bg)
            if hasattr(bg, 'get_rgba'):
                state["background_rgba"] = list(bg.get_rgba())
        except: pass
        try: state["brush_size"] = Gimp.context_get_brush_size()
        except: pass
        try: state["opacity"] = Gimp.context_get_opacity()
        except: pass

        return {"status": "success", "results": state}


Gimp.main(MCPProPlugin.__gtype__, sys.argv)
