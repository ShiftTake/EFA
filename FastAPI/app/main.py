
from fastapi import FastAPI

from .users import router as users_router
from .clip import router as clip_router

app = FastAPI()

app.include_router(users_router)
app.include_router(clip_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to EditForAll API"}
