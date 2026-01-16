from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, teams, tasks, users, tags, dependencies
from app.middleware import error_handler, performance_middleware

app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="A comprehensive task management system with team collaboration features"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(error_handler)
app.middleware("http")(performance_middleware)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(dependencies.router)

@app.get("/")
def read_root():
    return {"message": "Task Manager is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}