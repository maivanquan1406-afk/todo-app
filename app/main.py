from fastapi import FastAPI
from app.routers import todos
from app.db import init_db
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(todos.router, prefix="/api/v1/todos")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
