"""
Main MCP server implementation for Blender integration.

This module implements the Model Context Protocol server that acts as a bridge
between AI assistants and Blender, enabling AI-powered 3D modeling and automation.
"""

import asyncio
import json
import logging
import socket
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
    Resource,
    TextContent,
    Tool,
)

from .tools import BlenderTools
from .resources import BlenderResources
from .utils import BlenderConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlenderMCPServer:
    """Main MCP server for Blender integration."""

    def __init__(self, host: str = "localhost", port: int = 9999):
        """Initialize the Blender MCP server.
        
        Args:
            host: Host address for Blender connection
            port: Port for Blender connection
        """
        self.host = host
        self.port = port
        self.server = Server("blender-mcp")
        self.blender_connection = BlenderConnection(host, port)
        self.tools = BlenderTools(self.blender_connection)
        self.resources = BlenderResources(self.blender_connection)
        
        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available Blender tools."""
            return [
                Tool(
                    name="create_object",
                    description="Create a 3D object in Blender",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_type": {
                                "type": "string",
                                "enum": ["cube", "sphere", "cylinder", "cone", "plane", "monkey"],
                                "description": "Type of object to create"
                            },
                            "location": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Location coordinates [x, y, z]",
                                "default": [0, 0, 0]
                            },
                            "scale": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Scale factors [x, y, z]",
                                "default": [1, 1, 1]
                            },
                            "rotation": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Rotation angles in radians [x, y, z]",
                                "default": [0, 0, 0]
                            }
                        },
                        "required": ["object_type"]
                    }
                ),
                Tool(
                    name="delete_object",
                    description="Delete an object from the Blender scene",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Name of the object to delete"
                            }
                        },
                        "required": ["object_name"]
                    }
                ),
                Tool(
                    name="modify_object",
                    description="Modify properties of an existing object",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Name of the object to modify"
                            },
                            "location": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "New location coordinates [x, y, z]"
                            },
                            "scale": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "New scale factors [x, y, z]"
                            },
                            "rotation": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "New rotation angles in radians [x, y, z]"
                            }
                        },
                        "required": ["object_name"]
                    }
                ),
                Tool(
                    name="create_material",
                    description="Create and apply a material to an object",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Name of the object to apply material to"
                            },
                            "material_name": {
                                "type": "string",
                                "description": "Name for the new material"
                            },
                            "color": {
                                "type": "array",
                                "items": {"type": "number", "minimum": 0, "maximum": 1},
                                "minItems": 4,
                                "maxItems": 4,
                                "description": "RGBA color values [r, g, b, a]",
                                "default": [0.8, 0.8, 0.8, 1.0]
                            },
                            "metallic": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Metallic factor",
                                "default": 0.0
                            },
                            "roughness": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Roughness factor",
                                "default": 0.5
                            }
                        },
                        "required": ["object_name", "material_name"]
                    }
                ),
                Tool(
                    name="setup_lighting",
                    description="Set up lighting in the scene",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lighting_type": {
                                "type": "string",
                                "enum": ["studio", "outdoor", "dramatic", "soft"],
                                "description": "Type of lighting setup"
                            },
                            "strength": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Light strength/intensity",
                                "default": 1.0
                            }
                        },
                        "required": ["lighting_type"]
                    }
                ),
                Tool(
                    name="setup_camera",
                    description="Position and configure the camera",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Camera location [x, y, z]"
                            },
                            "target": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Point to look at [x, y, z]",
                                "default": [0, 0, 0]
                            },
                            "lens": {
                                "type": "number",
                                "minimum": 1,
                                "maximum": 200,
                                "description": "Camera lens focal length in mm",
                                "default": 50
                            },
                            "view_type": {
                                "type": "string",
                                "enum": ["perspective", "orthographic"],
                                "description": "Camera view type",
                                "default": "perspective"
                            }
                        },
                        "required": ["location"]
                    }
                ),
                Tool(
                    name="execute_python",
                    description="Execute arbitrary Python code in Blender",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute in Blender"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="render_scene",
                    description="Render the current scene",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Path to save the rendered image"
                            },
                            "resolution": {
                                "type": "array",
                                "items": {"type": "integer", "minimum": 1},
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Render resolution [width, height]",
                                "default": [1920, 1080]
                            },
                            "samples": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Number of render samples",
                                "default": 128
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "create_object":
                    result = await self.tools.create_object(**arguments)
                elif name == "delete_object":
                    result = await self.tools.delete_object(**arguments)
                elif name == "modify_object":
                    result = await self.tools.modify_object(**arguments)
                elif name == "create_material":
                    result = await self.tools.create_material(**arguments)
                elif name == "setup_lighting":
                    result = await self.tools.setup_lighting(**arguments)
                elif name == "setup_camera":
                    result = await self.tools.setup_camera(**arguments)
                elif name == "execute_python":
                    result = await self.tools.execute_python(**arguments)
                elif name == "render_scene":
                    result = await self.tools.render_scene(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return CallToolResult(
                    content=[TextContent(type="text", text=str(result))]
                )
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )

        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available resources."""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="scene://info",
                        name="Scene Information",
                        description="Get information about the current Blender scene",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="objects://list",
                        name="Object List",
                        description="List all objects in the scene",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="materials://list",
                        name="Material List",
                        description="List all materials in the scene",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="camera://info",
                        name="Camera Information",
                        description="Get camera settings and position",
                        mimeType="application/json"
                    )
                ]
            )

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Handle resource reading."""
            try:
                if uri == "scene://info":
                    data = await self.resources.get_scene_info()
                elif uri == "objects://list":
                    data = await self.resources.get_objects_list()
                elif uri == "materials://list":
                    data = await self.resources.get_materials_list()
                elif uri == "camera://info":
                    data = await self.resources.get_camera_info()
                else:
                    raise ValueError(f"Unknown resource: {uri}")

                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(data, indent=2)
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    ]
                )

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Blender MCP Server...")
        
        # Test connection to Blender
        try:
            await self.blender_connection.test_connection()
            logger.info("Successfully connected to Blender")
        except Exception as e:
            logger.warning(f"Could not connect to Blender: {e}")
            logger.info("Make sure Blender is running with the MCP addon enabled")

        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="blender-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )


async def main() -> None:
    """Main entry point for the server."""
    server = BlenderMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 