from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import videos
from app.db.session import init_db

app = FastAPI(title="AI Video Stylization API")

@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Video Stylization API"}

app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
