#!/usr/bin/env python3
"""
Basic usage example for Blender MCP server.

This script demonstrates how to use the MCP server to interact with Blender
programmatically through the Model Context Protocol.
"""

import asyncio
import json
from src.blender_mcp.utils import BlenderConnection


async def main():
    """Main example function."""
    # Create connection to Blender
    connection = BlenderConnection("localhost", 9999)
    
    print("Testing connection to Blender...")
    
    try:
        # Test connection
        if await connection.test_connection():
            print("✓ Connected to Blender successfully!")
        else:
            print("✗ Failed to connect to Blender")
            print("Make sure Blender is running with the MCP addon enabled")
            return
        
        # Get Blender info
        print("\nGetting Blender information...")
        blender_info = await connection.get_blender_info()
        print(f"Blender Version: {blender_info.get('version', 'Unknown')}")
        print(f"Current Scene: {blender_info.get('scene_name', 'Unknown')}")
        
        # Create some objects
        print("\nCreating objects...")
        
        # Create a cube
        cube_script = """
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "MCP_Cube"

print(f"Created cube: {cube.name}")
"""
        
        result = await connection.execute_script(cube_script)
        if result.get("status") == "success":
            print("✓ Created cube")
        else:
            print(f"✗ Failed to create cube: {result.get('message')}")
        
        # Create a sphere
        sphere_script = """
import bpy

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
sphere = bpy.context.active_object
sphere.name = "MCP_Sphere"

print(f"Created sphere: {sphere.name}")
"""
        
        result = await connection.execute_script(sphere_script)
        if result.get("status") == "success":
            print("✓ Created sphere")
        else:
            print(f"✗ Failed to create sphere: {result.get('message')}")
        
        # Add materials
        print("\nAdding materials...")
        
        material_script = """
import bpy

# Create red material for cube
red_mat = bpy.data.materials.new(name="Red_Material")
red_mat.use_nodes = True
bsdf = red_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)  # Red
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.3

# Apply to cube
cube = bpy.data.objects.get("MCP_Cube")
if cube:
    cube.data.materials.append(red_mat)
    print("Applied red material to cube")

# Create blue material for sphere
blue_mat = bpy.data.materials.new(name="Blue_Material")
blue_mat.use_nodes = True
bsdf = blue_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 1.0, 1.0)  # Blue
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.1

# Apply to sphere
sphere = bpy.data.objects.get("MCP_Sphere")
if sphere:
    sphere.data.materials.append(blue_mat)
    print("Applied blue material to sphere")
"""
        
        result = await connection.execute_script(material_script)
        if result.get("status") == "success":
            print("✓ Added materials")
        else:
            print(f"✗ Failed to add materials: {result.get('message')}")
        
        # Set up lighting
        print("\nSetting up lighting...")
        
        lighting_script = """
import bpy

# Clear existing lights
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

# Add key light
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
key_light = bpy.context.active_object
key_light.data.energy = 100
key_light.data.size = 2
key_light.name = "Key_Light"

# Add fill light
bpy.ops.object.light_add(type='AREA', location=(-4, -2, 4))
fill_light = bpy.context.active_object
fill_light.data.energy = 50
fill_light.data.size = 3
fill_light.name = "Fill_Light"

print("Set up studio lighting")
"""
        
        result = await connection.execute_script(lighting_script)
        if result.get("status") == "success":
            print("✓ Set up lighting")
        else:
            print(f"✗ Failed to set up lighting: {result.get('message')}")
        
        # Position camera
        print("\nPositioning camera...")
        
        camera_script = """
import bpy
from mathutils import Vector

# Get or create camera
camera = bpy.context.scene.camera
if not camera:
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object

# Position camera
camera.location = (7, -7, 5)

# Point camera at origin
direction = Vector((0, 0, 0)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Set camera properties
camera.data.lens = 50
camera.name = "MCP_Camera"

print(f"Positioned camera at {list(camera.location)}")
"""
        
        result = await connection.execute_script(camera_script)
        if result.get("status") == "success":
            print("✓ Positioned camera")
        else:
            print(f"✗ Failed to position camera: {result.get('message')}")
        
        # Get scene information
        print("\nGetting scene information...")
        
        scene_info_script = """
import bpy

scene = bpy.context.scene

info = {
    "objects": len(scene.objects),
    "meshes": len([obj for obj in scene.objects if obj.type == 'MESH']),
    "lights": len([obj for obj in scene.objects if obj.type == 'LIGHT']),
    "cameras": len([obj for obj in scene.objects if obj.type == 'CAMERA']),
    "materials": len(bpy.data.materials)
}

print("SCENE_INFO:", info)
"""
        
        result = await connection.execute_script(scene_info_script)
        if result.get("status") == "success":
            output = result.get("result", "")
            if "SCENE_INFO:" in output:
                info_str = output.split("SCENE_INFO:")[1].strip()
                try:
                    scene_info = eval(info_str)
                    print(f"Scene contains:")
                    print(f"  - {scene_info['objects']} total objects")
                    print(f"  - {scene_info['meshes']} meshes")
                    print(f"  - {scene_info['lights']} lights")
                    print(f"  - {scene_info['cameras']} cameras")
                    print(f"  - {scene_info['materials']} materials")
                except:
                    print("Could not parse scene info")
        
        print("\n✓ Example completed successfully!")
        print("Check your Blender viewport to see the created scene.")
        
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 