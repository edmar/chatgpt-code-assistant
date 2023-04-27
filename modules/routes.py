from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
import trafilatura
from pathlib import Path
from requests_html import AsyncHTMLSession
from .models import CreateFileRequestBody, AnalyzeCodeRequestBody, RefactorCodeRequestBody
import subprocess
import autopep8
from .utils import execute_command
import json

app = FastAPI()

@app.get("/")
async def hello_world():
    return "hello, welcome to chatgpt Code Assistant plugin!"

@app.get("/url")
async def get_url_content(url: str):
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

@app.get("/file")
async def get_file_content(filepath: str):
    try:
        file_path = Path(filepath)
        if not file_path.is_absolute():
            raise HTTPException(
                status_code=400, detail="Only absolute file paths are allowed.")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found.")
        if not file_path.is_file():
            raise HTTPException(
                status_code=400, detail="The path provided is not a file.")

        with file_path.open("r") as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

@app.post("/create-file")
async def create_file(request_body: CreateFileRequestBody = Body(...)):
    filepath = request_body.filepath
    content = request_body.content

    root_path = Path(__file__).parent.resolve()

    # Create a Path object from the filepath
    file_path = root_path / filepath

    # Create the file and write the content to it
    with file_path.open("w") as file:
        file.write(content)
    return JSONResponse(content={"status": "success", "message": "File created successfully."}, status_code=201)

@app.post("/analyze-code", tags=["Code Analysis"], summary="Analyze code and provide statistics")
async def analyze_code(request_body: AnalyzeCodeRequestBody = Body(...)):
    filepath = request_body.filepath
    file_path = Path(filepath)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    if not file_path.is_file():
        raise HTTPException(
            status_code=400, detail="The path provided is not a file.")

    result = subprocess.run(
        ["flake8", "--statistics", filepath], capture_output=True, text=True)
    output = result.stdout + result.stderr

    return JSONResponse(content={"output": output}, status_code=200)

@app.post("/refactor-code", tags=["Code Refactoring"], summary="Refactor code using autopep8")
async def refactor_code(request_body: RefactorCodeRequestBody = Body(...)):
	filepath=request_body.filepath
	file_path=Path(filepath)
		
	if not file_path.exists():
		raise HTTPException(status_code=404, detail="File not found.")
	if not file_path.is_file():
		raise HTTPException(
			status_code=400, detail="The path provided is not a file.")

	with file_path.open("r") as file:
		original_code = file.read()

	refactored_code = autopep8.fix_code(original_code)

	with file_path.open("w") as file:
		file.write(refactored_code)

	return JSONResponse(content={"status": "success", "message": "Code refactored successfully."}, status_code=200)

@app.get("/logo.png")
async def plugin_logo():
	return FileResponse("logo.png")


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest(request: Request):
    host = request.headers["host"]
    with open("ai-plugin.json") as f:
        text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
    return JSONResponse(content=json.loads(text))
