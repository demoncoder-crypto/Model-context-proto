"""
Blender resources implementation for MCP server.

This module provides resources that AI assistants can read to get information
about the current Blender scene, objects, materials, and other scene data.
"""

import json
import logging
from typing import Any, Dict, List

from .utils import BlenderConnection

logger = logging.getLogger(__name__)


class BlenderResources:
    """Resources for reading Blender scene information."""

    def __init__(self, connection: BlenderConnection):
        """Initialize Blender resources.
        
        Args:
            connection: Connection to Blender
        """
        self.connection = connection

    async def get_scene_info(self) -> Dict[str, Any]:
        """Get general information about the current Blender scene.
        
        Returns:
            Scene information dictionary
        """
        code = """
import bpy

scene = bpy.context.scene

# Get basic scene info
scene_info = {
    "name": scene.name,
    "frame_current": scene.frame_current,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "render_engine": scene.render.engine,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "object_count": len(scene.objects),
    "material_count": len(bpy.data.materials),
    "mesh_count": len(bpy.data.meshes),
    "light_count": len([obj for obj in scene.objects if obj.type == 'LIGHT']),
    "camera_count": len([obj for obj in scene.objects if obj.type == 'CAMERA']),
    "active_object": scene.objects.active.name if scene.objects.active else None
}

print("RESULT:", scene_info)
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
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get scene info"}

    async def get_objects_list(self) -> Dict[str, Any]:
        """Get a list of all objects in the scene.
        
        Returns:
            Objects list with detailed information
        """
        code = """
import bpy

objects_info = []

for obj in bpy.context.scene.objects:
    obj_info = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "visible": obj.visible_get(),
        "selected": obj.select_get(),
        "active": obj == bpy.context.active_object,
        "parent": obj.parent.name if obj.parent else None,
        "children": [child.name for child in obj.children],
        "material_count": len(obj.data.materials) if hasattr(obj.data, 'materials') else 0
    }
    
    # Add type-specific information
    if obj.type == 'MESH':
        obj_info["vertex_count"] = len(obj.data.vertices)
        obj_info["face_count"] = len(obj.data.polygons)
        obj_info["edge_count"] = len(obj.data.edges)
    elif obj.type == 'LIGHT':
        obj_info["light_type"] = obj.data.type
        obj_info["energy"] = obj.data.energy
    elif obj.type == 'CAMERA':
        obj_info["lens"] = obj.data.lens
        obj_info["camera_type"] = obj.data.type
    
    objects_info.append(obj_info)

result = {
    "objects": objects_info,
    "total_count": len(objects_info)
}

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
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get objects list"}

    async def get_materials_list(self) -> Dict[str, Any]:
        """Get a list of all materials in the scene.
        
        Returns:
            Materials list with properties
        """
        code = """
import bpy

materials_info = []

for mat in bpy.data.materials:
    mat_info = {
        "name": mat.name,
        "use_nodes": mat.use_nodes,
        "users": mat.users,
        "fake_user": mat.use_fake_user
    }
    
    # Get principled BSDF properties if using nodes
    if mat.use_nodes and mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            mat_info["base_color"] = list(bsdf.inputs["Base Color"].default_value)
            mat_info["metallic"] = bsdf.inputs["Metallic"].default_value
            mat_info["roughness"] = bsdf.inputs["Roughness"].default_value
            mat_info["alpha"] = bsdf.inputs["Alpha"].default_value
            
            # Check for connected textures
            connected_inputs = []
            for input_socket in bsdf.inputs:
                if input_socket.is_linked:
                    connected_inputs.append(input_socket.name)
            mat_info["connected_inputs"] = connected_inputs
    
    materials_info.append(mat_info)

result = {
    "materials": materials_info,
    "total_count": len(materials_info)
}

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
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get materials list"}

    async def get_camera_info(self) -> Dict[str, Any]:
        """Get information about cameras in the scene.
        
        Returns:
            Camera information
        """
        code = """
import bpy

cameras_info = []

for obj in bpy.context.scene.objects:
    if obj.type == 'CAMERA':
        cam_info = {
            "name": obj.name,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "lens": obj.data.lens,
            "type": obj.data.type,
            "clip_start": obj.data.clip_start,
            "clip_end": obj.data.clip_end,
            "is_active": obj == bpy.context.scene.camera
        }
        
        # Add orthographic scale if orthographic
        if obj.data.type == 'ORTHO':
            cam_info["ortho_scale"] = obj.data.ortho_scale
        
        cameras_info.append(cam_info)

# Get active camera info
active_camera = bpy.context.scene.camera
active_camera_info = None
if active_camera:
    active_camera_info = {
        "name": active_camera.name,
        "location": list(active_camera.location),
        "rotation": list(active_camera.rotation_euler),
        "lens": active_camera.data.lens,
        "type": active_camera.data.type
    }

result = {
    "cameras": cameras_info,
    "active_camera": active_camera_info,
    "total_count": len(cameras_info)
}

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
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get camera info"}

    async def get_lighting_info(self) -> Dict[str, Any]:
        """Get information about lighting in the scene.
        
        Returns:
            Lighting information
        """
        code = """
import bpy

lights_info = []

for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        light_info = {
            "name": obj.name,
            "type": obj.data.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "energy": obj.data.energy,
            "color": list(obj.data.color)
        }
        
        # Add type-specific properties
        if obj.data.type == 'SPOT':
            light_info["spot_size"] = obj.data.spot_size
            light_info["spot_blend"] = obj.data.spot_blend
        elif obj.data.type == 'AREA':
            light_info["size"] = obj.data.size
            light_info["shape"] = obj.data.shape
        elif obj.data.type == 'SUN':
            light_info["angle"] = obj.data.angle
        
        lights_info.append(light_info)

# Get world lighting info
world = bpy.context.scene.world
world_info = None
if world and world.use_nodes:
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        world_info = {
            "color": list(bg_node.inputs["Color"].default_value[:3]),
            "strength": bg_node.inputs["Strength"].default_value
        }

result = {
    "lights": lights_info,
    "world_lighting": world_info,
    "total_lights": len(lights_info)
}

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
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get lighting info"}

    async def get_render_settings(self) -> Dict[str, Any]:
        """Get current render settings.
        
        Returns:
            Render settings information
        """
        code = """
import bpy

scene = bpy.context.scene

render_info = {
    "engine": scene.render.engine,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "resolution_percentage": scene.render.resolution_percentage,
    "frame_range": [scene.frame_start, scene.frame_end],
    "current_frame": scene.frame_current,
    "fps": scene.render.fps,
    "output_path": scene.render.filepath,
    "file_format": scene.render.image_settings.file_format
}

# Add engine-specific settings
if scene.render.engine == 'CYCLES':
    render_info["cycles"] = {
        "samples": scene.cycles.samples,
        "preview_samples": scene.cycles.preview_samples,
        "device": scene.cycles.device,
        "use_denoising": scene.cycles.use_denoising
    }
elif scene.render.engine == 'BLENDER_EEVEE':
    render_info["eevee"] = {
        "taa_render_samples": scene.eevee.taa_render_samples,
        "taa_samples": scene.eevee.taa_samples,
        "use_bloom": scene.eevee.use_bloom,
        "use_ssr": scene.eevee.use_ssr
    }

print("RESULT:", render_info)
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
                    return eval(result_str)
                except:
                    pass
        
        return {"error": "Failed to get render settings"} 