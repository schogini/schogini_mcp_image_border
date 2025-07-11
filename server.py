from mcp.server import Server
from mcp.server.stdio import stdio_server
# from mcp.types import (
#     TextContent,
#     FileContent,
#     Tool,
# )
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
import requests

def fetch_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except Exception as e:
        return {"error": f"Failed to fetch image: {str(e)}"}

def error_exit(code, message):
    return {"error_code": code, "error": message}


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
    print("1")

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
                        # "image_as_url": {"type": "boolean", "default": False}
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
                        "num1": {
                            "type": "string",
                            "description": "first number to add.",
                        },
                        "num2": {
                            "type": "string",
                            "description": "second number to add.",
                        }
                    },
                    "required": ["num1", "num2"],
                },
            )
        ]

    import base64

    @server.call_tool()
    async def call_tool(name, arguments: dict) -> list:
        if name == "image-border":
            # print("2")
            image_url = arguments["image_url"]
            border_thickness = arguments["border_thickness"]
            border_color = arguments["border_color"]
            # image_as_url = arguments.get("image_as_url", False)
            # print(f"image_url: {image_url}")
            # print(f"image_as_url: {image_as_url}")
            # ans="AAAA"
            # return [TextContent(type="text", text=f"{ans}")]
            try:
                response = fetch_image(image_url)
                if isinstance(response, dict):  # error_exit returned
                    return [TextContent(type="text", text="Failed to fetch image.")]
            except Exception:
                return [TextContent(type="text", text="Error fetching image.")]

            try:
                img = Image.open(BytesIO(response.content)).convert("RGB")
            except Exception:
                return [TextContent(type="text", text="Error opening image.")]

            try:
                bordered_img = ImageOps.expand(img, border=border_thickness, fill=border_color)
            except Exception:
                return [TextContent(type="text", text="Error adding border.")]

            # ans="BBB"
            # return [TextContent(type="text", text=f"{ans}")]

            img_byte_array = BytesIO()
            bordered_img.save(img_byte_array, format="PNG")
            img_byte_array.seek(0)

            # ans="CCC"
            # return [TextContent(type="text", text=f"{ans}")]
            base64_image = base64.b64encode(img_byte_array.getvalue()).decode("utf-8")
            return [TextContent(type="text", text=base64_image)]
        else:
            num1 = arguments['num1']
            num2 = arguments['num2']
            ans = float(num1) + float(num2) + 100.0
            # ans = name
            return [TextContent(type="text", text=f"{ans}")]
            # return [TextContent(type="text", text=f"{arguments['greeting']} World!")]            


    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


if __name__ == "__main__":
    # print("Starting the MCP Server for image-border")
    asyncio.run(main())

