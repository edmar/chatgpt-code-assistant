from pydantic import BaseModel


class CreateFileRequestBody(BaseModel):
    filepath: str
    content: str


class AnalyzeCodeRequestBody(BaseModel):
    filepath: str


class RefactorCodeRequestBody(BaseModel):
    filepath: str
