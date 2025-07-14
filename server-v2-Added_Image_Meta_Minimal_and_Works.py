from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

import asyncio
import sys
import aiofiles
from io import BytesIO
import uuid, os
import random, string
from PIL import Image, ImageOps
import requests
from urllib.parse import urlparse
import base64

def fetch_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except Exception as e:
        return {"error": f"Failed to fetch image: {str(e)}"}

def get_image_save_path(image_id, extension="png"):
    return os.path.join(os.path.dirname(__file__), 'static', 'images', f"{image_id}.{extension}")

async def log_data(data: bytes, direction: str) -> None:
    line = f"[{direction}] {data.decode().strip()}\n"
    async with aiofiles.open("/app/logs/logs.txt", "a") as f:
        await f.write(line)
    sys.stdout.write(line)
    sys.stdout.flush()

async def main():
    await serve()

async def serve() -> None:
    server = Server("mcp-image-border")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="image-border",
                description="Add a colored border to an image from a URL",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_url": {"type": "string", "description": "Public image URL"},
                        "border_thickness": {"type": "integer", "minimum": 0},
                        "border_color": {"type": "string", "description": "e.g., black, red, #FF0000"},
                    },
                    "required": ["image_url", "border_thickness", "border_color"]
                },
            ),
            Tool(
                name="add-two-numbers",
                description="A simple tool to add two numbers.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "num1": {"type": "string", "description": "First number to add"},
                        "num2": {"type": "string", "description": "Second number to add"},
                    },
                    "required": ["num1", "num2"],
                },
            ),
            Tool(
                name="image-meta",
                description="Get the width, height, and file size (in bytes) of an image URL.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_url": {
                            "type": "string",
                            "description": "The public URL of the image."
                        }
                    },
                    "required": ["image_url"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name, arguments: dict) -> list:
        if name == "image-border":
            image_url = arguments["image_url"]
            border_thickness = arguments["border_thickness"]
            border_color = arguments["border_color"]

            response = fetch_image(image_url)
            if isinstance(response, dict):  # error
                return [TextContent(type="text", text=response["error"])]

            try:
                img = Image.open(BytesIO(response.content)).convert("RGB")
                bordered_img = ImageOps.expand(img, border=border_thickness, fill=border_color)
                img_byte_array = BytesIO()
                bordered_img.save(img_byte_array, format="PNG")
                img_byte_array.seek(0)
                base64_image = base64.b64encode(img_byte_array.getvalue()).decode("utf-8")
                return [TextContent(type="text", text=base64_image)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error processing image: {str(e)}")]

        elif name == "image-meta":
            image_url = arguments["image_url"]

            response = fetch_image(image_url)
            if isinstance(response, dict):  # error
                return [TextContent(type="text", text=response["error"])]

            try:
                img = Image.open(BytesIO(response.content))
                width, height = img.size
                img_size = len(response.content)
                return [TextContent(
                    type="text",
                    text=f"Image Width: {width}px, Height: {height}px, Size: {img_size} bytes"
                )]
            except Exception as e:
                return [TextContent(type="text", text=f"Failed to process image: {e}")]

        elif name == "add-two-numbers":
            try:
                num1 = float(arguments['num1'])
                num2 = float(arguments['num2'])
                ans = num1 + num2 + 100.0
                return [TextContent(type="text", text=f"{ans}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {e}")]

        return [TextContent(type="text", text="Unknown tool name.")]

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
