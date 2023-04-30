from typing import List, Dict, Tuple, Optional
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
from dotenv import load_dotenv
import os
import subprocess


import openai
from chat_completion_utils import llm

load_dotenv()

# -> We'll use openai for generating git commit messages and such
openai.api_key = os.getenv("OPENAI_API_KEY")



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



# ===========================================
# Retrieve
# ===========================================

# Routes
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
    session = AsyncHTMLSession()
    response = await session.get(url)

    # Render the JavaScript on the page
    await response.html.arender()

    html_content = response.html.html

    # Extract the article using trafilatura (optional)
    article = trafilatura.extract(html_content)

    await session.close()

    return JSONResponse(content=article, status_code=200)


# ===========================================
# Create
# ===========================================

# Routes
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


# ===========================================
# Delete
# ===========================================


# ===========================================
# Git
# ===========================================

# TODO Extract to dedicated file

# Utils
# -------------------------------------------

def generate_commit_message(diff: str) -> str:
    system_instruction = "Generate a brief Git commit message based on the following diff. Do not include introductory text or explain what you have done. Only output the commit message you generate."
    user_input = diff
    message = llm(system_instruction=system_instruction, user_input=user_input)
    return message.strip()


def git_commit(commit_message: Optional[str] = None) -> None:
    try:
        subprocess.run(["git", "add", "-A"])
        if not commit_message:
            diff = subprocess.check_output(["git", "diff", "--staged"]).decode("utf-8")
            commit_message = generate_commit_message(diff)

        subprocess.run(["git", "commit", "-m", commit_message])
        return {"status": "success", "message": "Git commit created successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Error creating git commit: {e}"}


def git_reset_to_previous(num_commits: int = 1):
    try:
        subprocess.run(["git", "reset", "--hard", f"HEAD~{num_commits}"])
        return {"status": "success", "message": f"Reset to {num_commits} commit(s) before successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Error resetting to previous commit: {e}"}


def git_list_branches() -> Dict[str, List[str]]:
    try:
        output = subprocess.check_output(["git", "branch"]).decode("utf-8").strip()
        branches = [b.strip() for b in output.split("\n")]
        return {"status": "success", "branches": branches}
    except Exception as e:
        return {"status": "error", "message": f"Error getting the branch list: {e}"}


def git_create_branch(branch_name: str) -> Dict[str, str]:
    try:
        subprocess.run(["git", "checkout", "-b", branch_name])
        return {"status": "success", "message": f"Branch '{branch_name}' created and switched to."}
    except Exception as e:
        return {"status": "error", "message": f"Error creating branch '{branch_name}': {e}"}


def git_delete_branch(branch_name: str) -> Dict[str, str]:
    try:
        subprocess.run(["git", "branch", "-D", branch_name])
        return {"status": "success", "message": f"Branch '{branch_name}' deleted."}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting branch '{branch_name}': {e}"}


def git_switch_branch(branch_name: str) -> Dict[str, str]:
    try:
        subprocess.run(["git", "checkout", branch_name])
        return {"status": "success", "message": f"Switched to branch '{branch_name}'."}
    except Exception as e:
        return {"status": "error", "message": f"Error switching to branch '{branch_name}': {e}"}

def git_current_branch() -> Dict[str, str]:
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        return {"status": "success", "branch": branch}
    except Exception as e:
        return {"status": "error", "message": f"Error getting the current branch: {e}"}


def git_check_uncommitted_changes() -> Dict[str, str]:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
        changes = output.split('\n') if output else []
        return {"status": "success", "changes": changes}
    except Exception as e:
        return {"status": "error", "message": f"Error checking for uncommitted changes: {e}"}


# Routes
# -------------------------------------------

@app.post("/create-git-commit")
async def create_git_commit(commit_message: str = Body(..., embed=True)):
    """
    Create a git commit with the given commit message.
    """
    result = git_commit(commit_message=commit_message)
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])

@app.post("/rollback-update")
async def rollback_update(num_commits: int = 1):
    """
    Rollback a specified number of changes made by 'update_file'
    """
    result = git_reset_to_previous(num_commits=num_commits)
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@app.post("/create-git-branch")
async def create_git_branch(branch_name: str = Body(..., embed=True)):
    """
    Create a new git branch and switch to it.
    """
    result = git_create_branch(branch_name=branch_name)
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@app.delete("/delete-git-branch")
async def delete_git_branch(branch_name: str = Body(..., embed=True)):
    """
    Delete the specified git branch.
    """
    result = git_delete_branch(branch_name=branch_name)
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@app.post("/switch-git-branch")
async def switch_git_branch(branch_name: str = Body(..., embed=True)):
    """
    Switch to the specified git branch.
    """
    result = git_switch_branch(branch_name=branch_name)
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])

@app.get("/list-git-branches")
async def list_git_branches():
    """
    Get a list of all git branches.
    """
    result = git_list_branches()
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@app.get("/current-git-branch")
async def current_git_branch():
    """
    Get the current git branch.
    """
    result = git_current_branch()
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@app.get("/uncommitted-git-changes")
async def uncommitted_git_changes():
    """
    Check for uncommitted git changes.
    """
    result = git_check_uncommitted_changes()
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


# ===========================================
# Update 
# ===========================================

# Utils
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


# Routes
# -------------------------------------------

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

        git_commit() # Make a git commit before modifying the file content

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
