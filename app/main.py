from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth

app = FastAPI(title="Task Manager", version="1.0.0")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Task Manager is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}