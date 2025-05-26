"""
Utility functions and classes for Blender MCP server.

This module contains helper functions and the BlenderConnection class
that manages communication with the Blender addon.
"""

import asyncio
import json
import logging
import socket
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BlenderConnection:
    """Manages connection and communication with Blender addon."""

    def __init__(self, host: str = "localhost", port: int = 9999):
        """Initialize Blender connection.
        
        Args:
            host: Host address for Blender connection
            port: Port for Blender connection
        """
        self.host = host
        self.port = port
        self.timeout = 30.0  # 30 second timeout

    async def test_connection(self) -> bool:
        """Test if we can connect to Blender.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = await self.send_command({"type": "ping"})
            return response.get("status") == "success"
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False

    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to Blender and get the response.
        
        Args:
            command: Command dictionary to send
            
        Returns:
            Response dictionary from Blender
            
        Raises:
            ConnectionError: If unable to connect to Blender
            TimeoutError: If command times out
        """
        try:
            # Create connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )
            
            try:
                # Send command
                command_json = json.dumps(command) + "\n"
                writer.write(command_json.encode('utf-8'))
                await writer.drain()
                
                # Read response
                response_data = await asyncio.wait_for(
                    reader.readline(),
                    timeout=self.timeout
                )
                
                if not response_data:
                    raise ConnectionError("No response from Blender")
                
                response = json.loads(response_data.decode('utf-8').strip())
                return response
                
            finally:
                writer.close()
                await writer.wait_closed()
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"Command timed out after {self.timeout} seconds")
        except ConnectionRefusedError:
            raise ConnectionError(
                f"Could not connect to Blender at {self.host}:{self.port}. "
                "Make sure Blender is running with the MCP addon enabled."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Blender: {e}")
        except Exception as e:
            raise ConnectionError(f"Communication error with Blender: {e}")

    async def execute_script(self, script: str) -> Dict[str, Any]:
        """Execute a Python script in Blender.
        
        Args:
            script: Python script to execute
            
        Returns:
            Execution result
        """
        return await self.send_command({
            "type": "execute_code",
            "code": script
        })

    async def get_blender_info(self) -> Dict[str, Any]:
        """Get basic information about the Blender instance.
        
        Returns:
            Blender information
        """
        script = """
import bpy

info = {
    "version": bpy.app.version_string,
    "build_date": bpy.app.build_date.decode('utf-8'),
    "build_time": bpy.app.build_time.decode('utf-8'),
    "build_platform": bpy.app.build_platform.decode('utf-8'),
    "current_file": bpy.data.filepath,
    "scene_name": bpy.context.scene.name
}

print("RESULT:", info)
"""
        
        response = await self.execute_script(script)
        
        if response.get("status") == "success":
            output = response.get("result", "")
            if "RESULT:" in output:
                result_str = output.split("RESULT:")[1].strip()
                try:
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get Blender info"}


def format_blender_error(error_message: str) -> str:
    """Format Blender error messages for better readability.
    
    Args:
        error_message: Raw error message from Blender
        
    Returns:
        Formatted error message
    """
    # Remove common Blender traceback noise
    lines = error_message.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip empty lines and common traceback headers
        if not line.strip():
            continue
        if line.strip().startswith('Traceback'):
            continue
        if line.strip().startswith('File "<string>"'):
            continue
            
        cleaned_lines.append(line.strip())
    
    return '\n'.join(cleaned_lines) if cleaned_lines else error_message


def validate_blender_object_name(name: str) -> bool:
    """Validate if a string is a valid Blender object name.
    
    Args:
        name: Object name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Blender object names can't be empty and have some restrictions
    if len(name.strip()) == 0:
        return False
    
    # Check for invalid characters (basic validation)
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False
    
    return True


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def normalize_color(color: list) -> list:
    """Normalize color values to 0-1 range.
    
    Args:
        color: Color values (can be 0-255 or 0-1 range)
        
    Returns:
        Normalized color values (0-1 range)
    """
    if not color or len(color) < 3:
        return [0.8, 0.8, 0.8, 1.0]  # Default gray
    
    # Check if values are in 0-255 range
    if any(val > 1.0 for val in color[:3]):
        # Convert from 0-255 to 0-1
        normalized = [val / 255.0 for val in color[:3]]
    else:
        normalized = color[:3]
    
    # Ensure we have alpha
    if len(color) > 3:
        alpha = color[3] if color[3] <= 1.0 else color[3] / 255.0
    else:
        alpha = 1.0
    
    return normalized + [alpha]


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians.
    
    Args:
        degrees: Angle in degrees
        
    Returns:
        Angle in radians
    """
    import math
    return math.radians(degrees)


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees.
    
    Args:
        radians: Angle in radians
        
    Returns:
        Angle in degrees
    """
    import math
    return math.degrees(radians)


class BlenderScriptBuilder:
    """Helper class to build Blender Python scripts."""
    
    def __init__(self):
        """Initialize script builder."""
        self.imports = set()
        self.code_blocks = []
        
    def add_import(self, module: str) -> None:
        """Add an import statement.
        
        Args:
            module: Module to import
        """
        self.imports.add(f"import {module}")
    
    def add_from_import(self, module: str, items: str) -> None:
        """Add a from-import statement.
        
        Args:
            module: Module to import from
            items: Items to import
        """
        self.imports.add(f"from {module} import {items}")
    
    def add_code(self, code: str) -> None:
        """Add a code block.
        
        Args:
            code: Code to add
        """
        self.code_blocks.append(code)
    
    def build(self) -> str:
        """Build the complete script.
        
        Returns:
            Complete Python script
        """
        script_parts = []
        
        # Add imports
        if self.imports:
            script_parts.extend(sorted(self.imports))
            script_parts.append("")  # Empty line after imports
        
        # Add code blocks
        script_parts.extend(self.code_blocks)
        
        return "\n".join(script_parts)


def create_safe_blender_script(code: str) -> str:
    """Wrap user code in a safe execution context.
    
    Args:
        code: User code to wrap
        
    Returns:
        Safe script with error handling
    """
    return f"""
try:
    {code}
except Exception as e:
    import traceback
    error_msg = f"Error: {{str(e)}}\\nTraceback: {{traceback.format_exc()}}"
    print("ERROR:", error_msg)
""" 