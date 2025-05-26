"""
Blender tools implementation for MCP server.

This module contains all the tools that can be called by AI assistants
to interact with Blender, including object creation, modification, and scene management.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from .utils import BlenderConnection

logger = logging.getLogger(__name__)


class BlenderTools:
    """Tools for interacting with Blender through the MCP server."""

    def __init__(self, connection: BlenderConnection):
        """Initialize Blender tools.
        
        Args:
            connection: Connection to Blender
        """
        self.connection = connection

    async def create_object(
        self,
        object_type: str,
        location: Optional[List[float]] = None,
        scale: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Create a 3D object in Blender.
        
        Args:
            object_type: Type of object to create
            location: Location coordinates [x, y, z]
            scale: Scale factors [x, y, z]
            rotation: Rotation angles in radians [x, y, z]
            
        Returns:
            Result of the operation
        """
        location = location or [0, 0, 0]
        scale = scale or [1, 1, 1]
        rotation = rotation or [0, 0, 0]

        # Map object types to Blender operations
        object_map = {
            "cube": "bpy.ops.mesh.primitive_cube_add",
            "sphere": "bpy.ops.mesh.primitive_uv_sphere_add",
            "cylinder": "bpy.ops.mesh.primitive_cylinder_add",
            "cone": "bpy.ops.mesh.primitive_cone_add",
            "plane": "bpy.ops.mesh.primitive_plane_add",
            "monkey": "bpy.ops.mesh.primitive_monkey_add"
        }

        if object_type not in object_map:
            raise ValueError(f"Unknown object type: {object_type}")

        code = f"""
import bpy
import bmesh
from mathutils import Vector, Euler

# Create the object
{object_map[object_type]}(location=({location[0]}, {location[1]}, {location[2]}))

# Get the active object (the one we just created)
obj = bpy.context.active_object

# Set scale
obj.scale = ({scale[0]}, {scale[1]}, {scale[2]})

# Set rotation
obj.rotation_euler = Euler(({rotation[0]}, {rotation[1]}, {rotation[2]}), 'XYZ')

# Update the scene
bpy.context.view_layer.update()

result = {{
    "success": True,
    "object_name": obj.name,
    "location": list(obj.location),
    "scale": list(obj.scale),
    "rotation": list(obj.rotation_euler)
}}

print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            # Parse the result from the output
            output = response.get("result", "")
            if "RESULT:" in output:
                result_str = output.split("RESULT:")[1].strip()
                try:
                    result = eval(result_str)  # Safe in this context
                    return result
                except:
                    pass
            
            return {
                "success": True,
                "message": f"Created {object_type} object",
                "output": output
            }
        else:
            raise Exception(f"Failed to create object: {response.get('message', 'Unknown error')}")

    async def delete_object(self, object_name: str) -> Dict[str, Any]:
        """Delete an object from the Blender scene.
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            Result of the operation
        """
        code = f"""
import bpy

# Find the object
obj = bpy.data.objects.get("{object_name}")

if obj is None:
    result = {{"success": False, "message": "Object '{object_name}' not found"}}
else:
    # Select and delete the object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.delete()
    result = {{"success": True, "message": "Object '{object_name}' deleted successfully"}}

print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            output = response.get("result", "")
            if "RESULT:" in output:
                result_str = output.split("RESULT:")[1].strip()
                try:
                    result = eval(result_str)
                    return result
                except:
                    pass
            
            return {"success": True, "message": f"Deleted object {object_name}"}
        else:
            raise Exception(f"Failed to delete object: {response.get('message', 'Unknown error')}")

    async def modify_object(
        self,
        object_name: str,
        location: Optional[List[float]] = None,
        scale: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Modify properties of an existing object.
        
        Args:
            object_name: Name of the object to modify
            location: New location coordinates [x, y, z]
            scale: New scale factors [x, y, z]
            rotation: New rotation angles in radians [x, y, z]
            
        Returns:
            Result of the operation
        """
        code = f"""
import bpy
from mathutils import Vector, Euler

# Find the object
obj = bpy.data.objects.get("{object_name}")

if obj is None:
    result = {{"success": False, "message": "Object '{object_name}' not found"}}
else:
    # Modify properties
    {f"obj.location = ({location[0]}, {location[1]}, {location[2]})" if location else ""}
    {f"obj.scale = ({scale[0]}, {scale[1]}, {scale[2]})" if scale else ""}
    {f"obj.rotation_euler = Euler(({rotation[0]}, {rotation[1]}, {rotation[2]}), 'XYZ')" if rotation else ""}
    
    # Update the scene
    bpy.context.view_layer.update()
    
    result = {{
        "success": True,
        "object_name": obj.name,
        "location": list(obj.location),
        "scale": list(obj.scale),
        "rotation": list(obj.rotation_euler)
    }}

print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            output = response.get("result", "")
            if "RESULT:" in output:
                result_str = output.split("RESULT:")[1].strip()
                try:
                    result = eval(result_str)
                    return result
                except:
                    pass
            
            return {"success": True, "message": f"Modified object {object_name}"}
        else:
            raise Exception(f"Failed to modify object: {response.get('message', 'Unknown error')}")

    async def create_material(
        self,
        object_name: str,
        material_name: str,
        color: Optional[List[float]] = None,
        metallic: float = 0.0,
        roughness: float = 0.5
    ) -> Dict[str, Any]:
        """Create and apply a material to an object.
        
        Args:
            object_name: Name of the object to apply material to
            material_name: Name for the new material
            color: RGBA color values [r, g, b, a]
            metallic: Metallic factor (0-1)
            roughness: Roughness factor (0-1)
            
        Returns:
            Result of the operation
        """
        color = color or [0.8, 0.8, 0.8, 1.0]

        code = f"""
import bpy

# Find the object
obj = bpy.data.objects.get("{object_name}")

if obj is None:
    result = {{"success": False, "message": "Object '{object_name}' not found"}}
else:
    # Create a new material
    mat = bpy.data.materials.new(name="{material_name}")
    mat.use_nodes = True
    
    # Get the principled BSDF node
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # Set material properties
        bsdf.inputs["Base Color"].default_value = ({color[0]}, {color[1]}, {color[2]}, {color[3]})
        bsdf.inputs["Metallic"].default_value = {metallic}
        bsdf.inputs["Roughness"].default_value = {roughness}
    
    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    result = {{
        "success": True,
        "object_name": obj.name,
        "material_name": mat.name,
        "color": {color},
        "metallic": {metallic},
        "roughness": {roughness}
    }}

print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            output = response.get("result", "")
            if "RESULT:" in output:
                result_str = output.split("RESULT:")[1].strip()
                try:
                    result = eval(result_str)
                    return result
                except:
                    pass
            
            return {"success": True, "message": f"Created material {material_name} for {object_name}"}
        else:
            raise Exception(f"Failed to create material: {response.get('message', 'Unknown error')}")

    async def setup_lighting(self, lighting_type: str, strength: float = 1.0) -> Dict[str, Any]:
        """Set up lighting in the scene.
        
        Args:
            lighting_type: Type of lighting setup
            strength: Light strength/intensity
            
        Returns:
            Result of the operation
        """
        lighting_setups = {
            "studio": """
# Studio lighting setup
import bpy

# Clear existing lights
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        obj.select_set(True)
bpy.ops.object.delete()

# Key light
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
key_light = bpy.context.active_object
key_light.data.energy = {strength} * 100
key_light.data.size = 2

# Fill light
bpy.ops.object.light_add(type='AREA', location=(-4, -2, 4))
fill_light = bpy.context.active_object
fill_light.data.energy = {strength} * 50
fill_light.data.size = 3

# Rim light
bpy.ops.object.light_add(type='SPOT', location=(0, 4, 6))
rim_light = bpy.context.active_object
rim_light.data.energy = {strength} * 75
""",
            "outdoor": """
# Outdoor lighting setup
import bpy

# Clear existing lights
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        obj.select_set(True)
bpy.ops.object.delete()

# Sun light
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun_light = bpy.context.active_object
sun_light.data.energy = {strength} * 5
sun_light.rotation_euler = (0.785, 0, 0.785)  # 45 degrees

# Sky light (area light for ambient)
bpy.ops.object.light_add(type='AREA', location=(0, 0, 8))
sky_light = bpy.context.active_object
sky_light.data.energy = {strength} * 20
sky_light.data.size = 10
""",
            "dramatic": """
# Dramatic lighting setup
import bpy

# Clear existing lights
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        obj.select_set(True)
bpy.ops.object.delete()

# Strong directional light
bpy.ops.object.light_add(type='SPOT', location=(6, -6, 8))
main_light = bpy.context.active_object
main_light.data.energy = {strength} * 200
main_light.data.spot_size = 0.5

# Weak fill light
bpy.ops.object.light_add(type='AREA', location=(-2, 2, 3))
fill_light = bpy.context.active_object
fill_light.data.energy = {strength} * 10
""",
            "soft": """
# Soft lighting setup
import bpy

# Clear existing lights
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        obj.select_set(True)
bpy.ops.object.delete()

# Large soft area lights
bpy.ops.object.light_add(type='AREA', location=(3, -3, 5))
light1 = bpy.context.active_object
light1.data.energy = {strength} * 30
light1.data.size = 4

bpy.ops.object.light_add(type='AREA', location=(-3, 3, 5))
light2 = bpy.context.active_object
light2.data.energy = {strength} * 30
light2.data.size = 4

bpy.ops.object.light_add(type='AREA', location=(0, 0, 8))
light3 = bpy.context.active_object
light3.data.energy = {strength} * 20
light3.data.size = 6
"""
        }

        if lighting_type not in lighting_setups:
            raise ValueError(f"Unknown lighting type: {lighting_type}")

        code = lighting_setups[lighting_type] + f"""

result = {{"success": True, "lighting_type": "{lighting_type}", "strength": {strength}}}
print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            return {"success": True, "message": f"Set up {lighting_type} lighting"}
        else:
            raise Exception(f"Failed to setup lighting: {response.get('message', 'Unknown error')}")

    async def setup_camera(
        self,
        location: List[float],
        target: Optional[List[float]] = None,
        lens: float = 50,
        view_type: str = "perspective"
    ) -> Dict[str, Any]:
        """Position and configure the camera.
        
        Args:
            location: Camera location [x, y, z]
            target: Point to look at [x, y, z]
            lens: Camera lens focal length in mm
            view_type: Camera view type
            
        Returns:
            Result of the operation
        """
        target = target or [0, 0, 0]

        code = f"""
import bpy
from mathutils import Vector
import bmesh

# Get the camera
camera = bpy.context.scene.camera
if camera is None:
    # Create a camera if none exists
    bpy.ops.object.camera_add(location=({location[0]}, {location[1]}, {location[2]}))
    camera = bpy.context.active_object
else:
    camera.location = ({location[0]}, {location[1]}, {location[2]})

# Set camera properties
camera.data.lens = {lens}
camera.data.type = '{"ORTHO" if view_type == "orthographic" else "PERSP"}'

# Point camera at target
direction = Vector(({target[0]}, {target[1]}, {target[2]})) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Update the scene
bpy.context.view_layer.update()

result = {{
    "success": True,
    "camera_location": list(camera.location),
    "target": {target},
    "lens": {lens},
    "view_type": "{view_type}"
}}

print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            return {"success": True, "message": "Camera positioned successfully"}
        else:
            raise Exception(f"Failed to setup camera: {response.get('message', 'Unknown error')}")

    async def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute arbitrary Python code in Blender.
        
        Args:
            code: Python code to execute
            
        Returns:
            Result of the execution
        """
        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            return {
                "success": True,
                "output": response.get("result", ""),
                "message": "Code executed successfully"
            }
        else:
            raise Exception(f"Failed to execute code: {response.get('message', 'Unknown error')}")

    async def render_scene(
        self,
        output_path: Optional[str] = None,
        resolution: Optional[List[int]] = None,
        samples: int = 128
    ) -> Dict[str, Any]:
        """Render the current scene.
        
        Args:
            output_path: Path to save the rendered image
            resolution: Render resolution [width, height]
            samples: Number of render samples
            
        Returns:
            Result of the render operation
        """
        resolution = resolution or [1920, 1080]
        output_path = output_path or "/tmp/blender_render.png"

        code = f"""
import bpy
import os

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = {resolution[0]}
scene.render.resolution_y = {resolution[1]}
scene.render.filepath = "{output_path}"

# Set cycles settings if using cycles
if scene.render.engine == 'CYCLES':
    scene.cycles.samples = {samples}

# Render the scene
bpy.ops.render.render(write_still=True)

result = {{
    "success": True,
    "output_path": "{output_path}",
    "resolution": {resolution},
    "samples": {samples}
}}

print("RESULT:", result)
"""

        response = await self.connection.send_command({
            "type": "execute_code",
            "code": code
        })

        if response.get("status") == "success":
            return {
                "success": True,
                "message": f"Scene rendered to {output_path}",
                "output_path": output_path
            }
        else:
            raise Exception(f"Failed to render scene: {response.get('message', 'Unknown error')}") 