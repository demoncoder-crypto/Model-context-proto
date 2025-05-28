import asyncio
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sys
import os
import textwrap

# Adjust path to import BlenderConnection from the parent directory's src folder
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.insert(0, project_root)

from src.blender_mcp.utils import BlenderConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blender_web_app")

app = FastAPI(
    title="Blender MCP Web Interface",
    description="A web interface to send commands to a running Blender MCP instance.",
    version="0.1.0"
)

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Pydantic model for request body
class BlenderCodeRequest(BaseModel):
    code: str

class NaturalLanguageCommandRequest(BaseModel):
    natural_language_command: str

# Global Blender connection (initialized on startup)
blender_conn: BlenderConnection

@app.on_event("startup")
async def startup_event():
    global blender_conn
    # Default Blender addon host and port
    # These should match what's configured in your Blender addon panel
    blender_host = os.getenv("BLENDER_HOST", "localhost") 
    blender_port = int(os.getenv("BLENDER_PORT", 9999))
    blender_conn = BlenderConnection(host=blender_host, port=blender_port)
    logger.info(f"FastAPI app started. Attempting to connect to Blender at {blender_host}:{blender_port}")
    
    # Test connection on startup (optional, but good for diagnostics)
    try:
        if await blender_conn.test_connection():
            logger.info("Successfully connected to Blender MCP addon server.")
        else:
            logger.warning("Could not connect to Blender MCP addon server on startup. Ensure Blender is running with the addon enabled and server started.")
    except Exception as e:
        logger.error(f"Error testing Blender connection on startup: {e}")
        logger.warning("Ensure Blender is running with the addon enabled and server started.")

@app.get("/", response_class=HTMLResponse)
async def get_landing_page(request: Request):
    """Serve the main HTML landing page."""
    index_path = os.path.join(current_dir, "static", "index.html")
    try:
        with open(index_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error(f"index.html not found at {index_path}")
        raise HTTPException(status_code=404, detail="Landing page not found. Ensure static files are correctly placed.")
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        raise HTTPException(status_code=500, detail="Could not load landing page.")

@app.post("/api/blender/interpret")
async def interpret_natural_language(request_data: NaturalLanguageCommandRequest):
    """API endpoint to interpret natural language and suggest Blender code."""
    command = request_data.natural_language_command
    logger.info(f"Received natural language command: {command}")

    # --- Placeholder for LLM Interaction --- 
    # In a real application, you would call an LLM here.
    # For now, we'll do very basic keyword matching.
    review_text = f"Interpreting command: '{command}'. (Placeholder LLM response)"
    
    # Properly embed the command string into the generated script
    # Use triple quotes for the script string and repr() for safe embedding of the command
    generated_script = f"""# Placeholder script - LLM would generate this
print(f"Command received: {command!r}")
""" # Using double quotes for the inner f-string to avoid clashes with repr()'s single quotes
    status = "success"

    if "cube" in command.lower():
        generated_script += "bpy.ops.mesh.primitive_cube_add()\n"
        review_text += "\nAction: Will attempt to create a cube."
    elif "sphere" in command.lower():
        generated_script += "bpy.ops.mesh.primitive_uv_sphere_add()\n"
        review_text += "\nAction: Will attempt to create a sphere."
    elif "cylinder" in command.lower():
        generated_script += "bpy.ops.mesh.primitive_cylinder_add()\n"
        review_text += "\nAction: Will attempt to create a cylinder."
        if "red" in command.lower():
            review_text += " (Color 'red' noted, but placeholder cannot apply color yet)."
        elif "blue" in command.lower():
            review_text += " (Color 'blue' noted, but placeholder cannot apply color yet)."
    elif "delete all" in command.lower():
        generated_script += ("import bpy\n" 
                           "if bpy.context.object and bpy.context.object.mode == 'EDIT':\n" 
                           "    bpy.ops.object.mode_set(mode='OBJECT')\n" 
                           "bpy.ops.object.select_all(action='SELECT')\n" 
                           "bpy.ops.object.delete()\n" 
                           "print('Deleted all objects.')\n")
        review_text += "\nAction: Will attempt to delete all objects."
    else:
        review_text += "\nAction: Could not determine a specific action from the command (using placeholder)."
        # No specific action, keep placeholder script.

    # Ensure bpy is imported if ops are used and not already in script
    if "bpy.ops" in generated_script and "import bpy" not in generated_script:
        generated_script = "import bpy\n" + generated_script
    # --- End of Placeholder LLM Interaction ---

    return {
        "status": status,
        "review": review_text,
        "generated_code": textwrap.dedent(generated_script) # Dedent here as well
    }

@app.post("/api/blender/execute")
async def execute_blender_code(request_data: BlenderCodeRequest):
    """API endpoint to execute Python code in Blender."""
    global blender_conn
    if not blender_conn:
        logger.error("Blender connection not initialized.")
        raise HTTPException(status_code=503, detail="Blender connection not available. Web server might be starting up or failed to connect.")

    logger.info(f"Received code to execute: {request_data.code[:100]}...") # Log first 100 chars
    
    try:
        dedented_code = textwrap.dedent(request_data.code)
        logger.info(f"Dedented code: {dedented_code[:100]}...") # Log dedented code

        # Send command to Blender addon's socket server
        response = await blender_conn.send_command({
            "type": "execute_code",
            "code": dedented_code
        })
        logger.info(f"Response from Blender: {response}")
        return response # Blender addon already returns a JSON serializable dict
    except ConnectionError as e:
        logger.error(f"Connection error with Blender: {e}")
        raise HTTPException(status_code=503, detail=f"Could not connect to Blender: {e}. Ensure Blender and the MCP addon server are running.")
    except TimeoutError as e:
        logger.error(f"Timeout error with Blender: {e}")
        raise HTTPException(status_code=504, detail=f"Command to Blender timed out: {e}")
    except ValueError as e: # Catches JSONDecodeError if response from Blender is bad
        logger.error(f"Value error (e.g., bad JSON from Blender): {e}")
        raise HTTPException(status_code=502, detail=f"Invalid response from Blender: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


if __name__ == "__main__":
    # This allows running directly with `python web_app.py`
    # For production, consider using a Gunicorn setup or similar.
    # Ensure Blender is running with the addon server started before running this.
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True) 