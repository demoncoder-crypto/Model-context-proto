#!/usr/bin/env python3
"""
Test script for Blender MCP server.

This script tests the basic functionality of the MCP server without requiring
a full MCP client setup.
"""

import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from blender_mcp.utils import BlenderConnection


async def test_connection():
    """Test basic connection to Blender."""
    print("🧪 Testing Blender MCP Server")
    print("=" * 40)
    
    connection = BlenderConnection("localhost", 9999)
    
    try:
        print("1. Testing connection...")
        if await connection.test_connection():
            print("   ✓ Connection successful!")
        else:
            print("   ✗ Connection failed!")
            print("   Make sure Blender is running with the MCP addon enabled")
            return False
        
        print("\n2. Getting Blender info...")
        info = await connection.get_blender_info()
        if "error" not in info:
            print(f"   ✓ Blender version: {info.get('version', 'Unknown')}")
            print(f"   ✓ Scene: {info.get('scene_name', 'Unknown')}")
        else:
            print("   ✗ Failed to get Blender info")
        
        print("\n3. Testing code execution...")
        test_script = """
import bpy
print("Hello from Blender!")
print(f"Current scene: {bpy.context.scene.name}")
print(f"Object count: {len(bpy.context.scene.objects)}")
"""
        
        result = await connection.execute_script(test_script)
        if result.get("status") == "success":
            print("   ✓ Code execution successful!")
            output = result.get("result", "").strip()
            if output:
                for line in output.split('\n'):
                    if line.strip():
                        print(f"   📝 {line}")
        else:
            print("   ✗ Code execution failed!")
            print(f"   Error: {result.get('message', 'Unknown error')}")
        
        print("\n4. Testing object creation...")
        create_script = """
import bpy

# Create a test cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

print(f"Created object: {cube.name}")
print(f"Location: {list(cube.location)}")
"""
        
        result = await connection.execute_script(create_script)
        if result.get("status") == "success":
            print("   ✓ Object creation successful!")
            output = result.get("result", "").strip()
            if output:
                for line in output.split('\n'):
                    if line.strip():
                        print(f"   📝 {line}")
        else:
            print("   ✗ Object creation failed!")
            print(f"   Error: {result.get('message', 'Unknown error')}")
        
        print("\n✅ All tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


async def main():
    """Main test function."""
    success = await test_connection()
    
    if success:
        print("\n🎉 Blender MCP Server is working correctly!")
        print("\nNext steps:")
        print("1. Configure your AI assistant (Claude/Cursor) with the MCP server")
        print("2. Try asking your AI to create 3D objects in Blender")
        print("3. Explore the examples in the examples/ directory")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure Blender is running")
        print("2. Install the blender_addon.py in Blender")
        print("3. Enable the 'Blender MCP' addon in Blender preferences")
        print("4. Start the MCP server in the Blender sidebar")
        print("5. Check that the server is running on localhost:9999")


if __name__ == "__main__":
    asyncio.run(main()) 