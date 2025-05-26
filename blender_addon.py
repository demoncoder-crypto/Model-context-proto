"""
Blender MCP Addon - Socket server for AI integration.

This addon creates a socket server within Blender that can receive and execute
commands from the MCP server, enabling AI-powered 3D modeling and automation.
"""

import bpy
import bmesh
import json
import socket
import threading
import time
import traceback
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel


bl_info = {
    "name": "Blender MCP",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Model Context Protocol integration for AI-powered 3D modeling",
    "category": "Interface",
}


class BlenderMCPServer:
    """Socket server that runs within Blender to handle MCP commands."""
    
    def __init__(self, host="localhost", port=9999):
        """Initialize the server.
        
        Args:
            host: Host address to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the server in a separate thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print(f"Blender MCP Server started on {self.host}:{self.port}")
        
    def stop(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("Blender MCP Server stopped")
        
    def _run_server(self):
        """Run the server loop."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    self._handle_client(client_socket)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Server error: {e}")
                    break
                    
        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                
    def _handle_client(self, client_socket):
        """Handle a client connection.
        
        Args:
            client_socket: Client socket connection
        """
        try:
            # Receive data
            data = client_socket.recv(4096).decode('utf-8').strip()
            if not data:
                return
                
            # Parse command
            try:
                command = json.loads(data)
            except json.JSONDecodeError:
                response = {"status": "error", "message": "Invalid JSON"}
                self._send_response(client_socket, response)
                return
                
            # Process command
            response = self._process_command(command)
            self._send_response(client_socket, response)
            
        except Exception as e:
            response = {"status": "error", "message": str(e)}
            self._send_response(client_socket, response)
        finally:
            client_socket.close()
            
    def _send_response(self, client_socket, response):
        """Send response to client.
        
        Args:
            client_socket: Client socket
            response: Response dictionary
        """
        try:
            response_json = json.dumps(response) + "\n"
            client_socket.send(response_json.encode('utf-8'))
        except Exception as e:
            print(f"Failed to send response: {e}")
            
    def _process_command(self, command):
        """Process a command from the client.
        
        Args:
            command: Command dictionary
            
        Returns:
            Response dictionary
        """
        command_type = command.get("type")
        
        if command_type == "ping":
            return {"status": "success", "message": "pong"}
        elif command_type == "execute_code":
            return self._execute_code(command.get("code", ""))
        else:
            return {"status": "error", "message": f"Unknown command type: {command_type}"}
            
    def _execute_code(self, code):
        """Execute Python code in Blender.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result
        """
        if not code:
            return {"status": "error", "message": "No code provided"}
            
        try:
            # Capture stdout
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                # Execute the code
                exec(code, {"bpy": bpy, "bmesh": bmesh})
                output = captured_output.getvalue()
                
                return {
                    "status": "success",
                    "result": output,
                    "message": "Code executed successfully"
                }
                
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }


# Global server instance
mcp_server = None


class BLENDERMCP_OT_start_server(Operator):
    """Start the Blender MCP server."""
    bl_idname = "blendermcp.start_server"
    bl_label = "Start MCP Server"
    bl_description = "Start the MCP server to enable AI integration"
    
    def execute(self, context):
        global mcp_server
        
        if mcp_server and mcp_server.running:
            self.report({'WARNING'}, "Server is already running")
            return {'CANCELLED'}
            
        try:
            props = context.scene.blendermcp_props
            mcp_server = BlenderMCPServer(props.host, props.port)
            mcp_server.start()
            
            self.report({'INFO'}, f"MCP Server started on {props.host}:{props.port}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to start server: {str(e)}")
            return {'CANCELLED'}


class BLENDERMCP_OT_stop_server(Operator):
    """Stop the Blender MCP server."""
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop MCP Server"
    bl_description = "Stop the MCP server"
    
    def execute(self, context):
        global mcp_server
        
        if not mcp_server or not mcp_server.running:
            self.report({'WARNING'}, "Server is not running")
            return {'CANCELLED'}
            
        try:
            mcp_server.stop()
            mcp_server = None
            
            self.report({'INFO'}, "MCP Server stopped")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to stop server: {str(e)}")
            return {'CANCELLED'}


class BLENDERMCP_OT_test_connection(Operator):
    """Test the MCP server connection."""
    bl_idname = "blendermcp.test_connection"
    bl_label = "Test Connection"
    bl_description = "Test if the MCP server is responding"
    
    def execute(self, context):
        global mcp_server
        
        if not mcp_server or not mcp_server.running:
            self.report({'WARNING'}, "Server is not running")
            return {'CANCELLED'}
            
        try:
            # Simple test by creating a test socket connection
            import socket
            props = context.scene.blendermcp_props
            
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5.0)
            
            try:
                test_socket.connect((props.host, props.port))
                test_command = json.dumps({"type": "ping"}) + "\n"
                test_socket.send(test_command.encode('utf-8'))
                
                response = test_socket.recv(1024).decode('utf-8')
                response_data = json.loads(response.strip())
                
                if response_data.get("status") == "success":
                    self.report({'INFO'}, "Connection test successful")
                else:
                    self.report({'WARNING'}, "Connection test failed")
                    
            finally:
                test_socket.close()
                
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Connection test failed: {str(e)}")
            return {'CANCELLED'}


class BlenderMCPProperties(bpy.types.PropertyGroup):
    """Properties for Blender MCP addon."""
    
    host: StringProperty(
        name="Host",
        description="Host address for the MCP server",
        default="localhost"
    )
    
    port: IntProperty(
        name="Port",
        description="Port for the MCP server",
        default=9999,
        min=1024,
        max=65535
    )
    
    auto_start: BoolProperty(
        name="Auto Start",
        description="Automatically start the server when Blender starts",
        default=False
    )


class BLENDERMCP_PT_panel(Panel):
    """Blender MCP control panel."""
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderMCP"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.blendermcp_props
        
        # Server settings
        box = layout.box()
        box.label(text="Server Settings", icon='SETTINGS')
        box.prop(props, "host")
        box.prop(props, "port")
        box.prop(props, "auto_start")
        
        # Server controls
        box = layout.box()
        box.label(text="Server Control", icon='PLAY')
        
        global mcp_server
        if mcp_server and mcp_server.running:
            box.label(text="Status: Running", icon='CHECKMARK')
            box.operator("blendermcp.stop_server", icon='PAUSE')
            box.operator("blendermcp.test_connection", icon='LINKED')
        else:
            box.label(text="Status: Stopped", icon='X')
            box.operator("blendermcp.start_server", icon='PLAY')
        
        # Information
        box = layout.box()
        box.label(text="Information", icon='INFO')
        box.label(text="Connect your AI assistant to:")
        box.label(text=f"{props.host}:{props.port}")
        
        # Quick actions
        box = layout.box()
        box.label(text="Quick Actions", icon='TOOL_SETTINGS')
        
        row = box.row()
        row.operator("mesh.primitive_cube_add", text="Add Cube", icon='MESH_CUBE')
        row.operator("mesh.primitive_uv_sphere_add", text="Add Sphere", icon='MESH_UVSPHERE')
        
        row = box.row()
        row.operator("object.delete", text="Delete", icon='X')
        row.operator("view3d.view_all", text="View All", icon='VIEWZOOM')


def auto_start_server():
    """Auto-start the server if enabled."""
    if hasattr(bpy.context.scene, 'blendermcp_props'):
        props = bpy.context.scene.blendermcp_props
        if props.auto_start:
            global mcp_server
            if not mcp_server or not mcp_server.running:
                try:
                    mcp_server = BlenderMCPServer(props.host, props.port)
                    mcp_server.start()
                    print(f"Auto-started MCP Server on {props.host}:{props.port}")
                except Exception as e:
                    print(f"Failed to auto-start MCP Server: {e}")


@bpy.app.handlers.persistent
def load_post_handler(dummy):
    """Handler called after loading a blend file."""
    # Delay auto-start to ensure everything is loaded
    bpy.app.timers.register(auto_start_server, first_interval=2.0)


classes = [
    BlenderMCPProperties,
    BLENDERMCP_OT_start_server,
    BLENDERMCP_OT_stop_server,
    BLENDERMCP_OT_test_connection,
    BLENDERMCP_PT_panel,
]


def register():
    """Register the addon."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.blendermcp_props = bpy.props.PointerProperty(type=BlenderMCPProperties)
    bpy.app.handlers.load_post.append(load_post_handler)
    
    print("Blender MCP addon registered")


def unregister():
    """Unregister the addon."""
    global mcp_server
    
    # Stop server if running
    if mcp_server and mcp_server.running:
        mcp_server.stop()
    
    # Remove handlers
    if load_post_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_handler)
    
    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.blendermcp_props
    
    print("Blender MCP addon unregistered")


if __name__ == "__main__":
    register() 