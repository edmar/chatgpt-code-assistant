import json
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import trafilatura
from pathlib import Path
from requests_html import AsyncHTMLSession


################################################
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
        allow_methods=['*'],
        allow_headers=['*'],
)

################################################
# ROUTES
################################################

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
            raise HTTPException(status_code=400, detail="Only absolute file paths are allowed.")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found.")
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="The path provided is not a file.")

        with file_path.open("r") as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")


@app.post("/create-file")
async def create_file(filepath: str = Body(...), content: str = Body(...)):
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
