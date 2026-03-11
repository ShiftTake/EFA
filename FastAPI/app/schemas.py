from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

class Clip(BaseModel):
    id: str
    title: str
    start: str
    score: int
    color: str
    sourceType: str
    sourceUrl: str
    fileName: str
    clipPath: str
