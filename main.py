from typing import List, Dict, Tuple
import json
from enum import Enum
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import trafilatura
from pathlib import Path
from requests_html import AsyncHTMLSession
from pydantic import BaseModel, Field
from fuzzywuzzy import fuzz



# CONFIG
################################################

app = FastAPI()
LOCALHOST_PORT=5002

# Add CORS for openapi domains to enable localhost plugin serving
origins = [
    "http://localhost",
    f"http://localhost:{LOCALHOST_PORT}",
    "https://chat.openai.com",
    "https://openai.com",
]
app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=['*'],
)

################################################
# ROUTES
################################################

@app.get("/hello")
async def hello_world():
    return "hello, and welcome to chatgpt Code Assistant plugin"


# -------------------------------------------
# Retrieve
# -------------------------------------------

@app.get("/file")
async def get_file_content(filepath: str):
    """
    Retrieve the content of a specified file.
    The function takes the file path as input and returns the content of the file.
    """

    try:
        file_path = validate_path(filepath)
        with file_path.open("r") as file:
            content = file.read()
        return {"content": content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")


@app.get("/url")
async def get_url_content(url: str):
    """
    Retrieve the content of a specified URL.
    The function takes the URL as input and returns the rendered HTML content of the page.
    Optionally, the extracted article content can also be returned.
    """
    # Create an AsyncHTML Session
    session = AsyncHTMLSession()

    # Send a GET request to the URL
    response = await session.get(url)

    # Render the JavaScript on the page
    await response.html.arender()

    # Extract the HTML content after rendering
    html_content = response.html.html

    # Extract the article using trafilatura (optional)
    article = trafilatura.extract(html_content)

    # Close the session
    await session.close()

    return JSONResponse(content=article, status_code=200)


# -------------------------------------------
# Create
# -------------------------------------------

@app.post("/create-file")
async def create_file(filepath: str = Body(...), content: str = Body(...)):
    """
    Create a new file with the specified content.
    Returns a status message indicating success or failure.
    """
    try:
        file_path = Path(filepath)
        if not file_path.is_absolute():
            raise HTTPException(status_code=400, detail="Only absolute file paths are allowed.")
        
        # Create the file and write the content to it
        with file_path.open("w") as file:
            file.write(content)
        return {"status": "success", "message": "File created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating file: {e}")

# -------------------------------------------
# Delete Content
# -------------------------------------------



# -------------------------------------------
# Update Content
# -------------------------------------------

class ActionType(Enum):
    INSERT = "insert"
    MODIFY = "modify"
    DELETE = "delete"

action_descriptions = {
    ActionType.INSERT: "Add new content below the matched line.",
    ActionType.MODIFY: "Update the content of the matched line.",
    ActionType.DELETE: "Remove the matched line.",
}

class UpdateMatch(BaseModel):
    content_to_match: str
    new_content: str
    action: ActionType = Field(
        ...,
        description="Action to perform on the matched content. Options: "
        + ", ".join([f"{item.name} - {action_descriptions[item]}" for item in ActionType])
    )

class UpdateLine(BaseModel):
    line_number: int
    new_content: str
    action: ActionType

def apply_updates(lines: List[str], updates: List[Tuple[int, ActionType, str]]) -> List[str]:
    line_offset = 0
    for line_number, action, new_content in updates:
        adjusted_line_number = line_number + line_offset
        if 0 <= adjusted_line_number < len(lines):
            if action == ActionType.INSERT:
                new_lines = new_content.splitlines()
                lines[adjusted_line_number + 1:adjusted_line_number + 1] = [new_line + "\n" for new_line in new_lines]
                line_offset += len(new_lines)
            elif action == ActionType.MODIFY:
                lines[adjusted_line_number] = new_content + "\n"
            elif action == ActionType.DELETE:
                del lines[adjusted_line_number]
                line_offset -= 1
    return lines


@app.post("/update-file")
async def update_file(
    filepath: str = Body(...),
    updates: List[UpdateMatch] = Body(...),
    use_fuzzy_match: bool = Body(True)
):
    """
    Update a file's content based on a specified pattern and action.
    Fuzzy match or exact match.
    Returns a status message indicating success or failure.
    """

    try:
        file_path = validate_path(filepath)

        with file_path.open("r") as file:
            lines = file.readlines()

        update_list = []
        for update in updates:
            if use_fuzzy_match:
                # Use fuzzy matching to find the best matching line
                best_match_score = 0
                best_match_index = None
                for i, line in enumerate(lines):
                    score = fuzz.ratio(update.content_to_match, line)
                    if score > best_match_score:
                        best_match_score = score
                        best_match_index = i
                matched_line_numbers = [best_match_index]
            else:
                # Use exact match
                matched_line_numbers = [i for i, line in enumerate(lines) if update.content_to_match in line]

            matched_line_numbers.sort(reverse=True)
            for line_number in matched_line_numbers:
                update_list.append((line_number, update.action, update.new_content))

        updated_lines = apply_updates(lines, update_list)

        with file_path.open("w") as file:
            file.writelines(updated_lines)

        return {"status": "success", "message": "File updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating file: {e}")


@app.post("/update-file-at-lines")
async def update_file_at_lines(filepath: str = Body(...), updates: List[UpdateLine] = Body(...)):
    """
    Update a file's content at specified line numbers based on the provided updates.
    Each update specifies the line number, new content, and action (insert, modify, or delete).
    This method should only be used when specifically indicated, as line numbers may change
    due to file modifications.
    """
    try:
        file_path = validate_path(filepath)

        with file_path.open("r") as file:
            lines = file.readlines()

        sorted_updates = sorted([(u.line_number, u.action, u.new_content) for u in updates], key=lambda x: x[0])
        updated_lines = apply_updates(lines, sorted_updates)

        with file_path.open("w") as file:
            file.writelines(updated_lines)

        return {"status": "success", "message": "File updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating file: {e}")


################################################
# UTILS
################################################

def validate_path(filepath: str) -> Path:
    file_path = Path(filepath)
    if not file_path.is_absolute():
        raise HTTPException(status_code=400, detail="Only absolute file paths are allowed.")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="The path provided is not a file.")
    return file_path


################################################
# BOILERPLATE
################################################

# Regenerate OpenAPI YAML when this file changes
def generate_openapi_spec():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Code Assistant",
        version="1.0",
        description="get url contents or a local file to help you with code",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


@app.get("/logo.png")
async def plugin_logo():
    return FileResponse("logo.png")


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest(request: Request):
    host = request.headers["host"]
    with open("ai-plugin.json") as f:
        text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
    return JSONResponse(content=json.loads(text))

@app.get("/openapi.json")
async def openapi_spec(request: Request):
    host = request.headers['host']
    with open("openapi.json") as f:
        text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
    return JSONResponse(content=text, media_type="text/json")



if __name__ == "__main__":
    import uvicorn
    app.openapi = generate_openapi_spec
    uvicorn.run("main:app", host="0.0.0.0", port=LOCALHOST_PORT, reload=True)
