from fastapi import FastAPI
from app.database import engine, Base

app = FastAPI(title="Task Management API", version="1.0.0")

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Task Management API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}