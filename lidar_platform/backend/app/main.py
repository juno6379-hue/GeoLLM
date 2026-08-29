from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

from .api.routes import classification
app.include_router(classification.router, prefix=f"{settings.API_V1_STR}/classification", tags=["Classification"])


@app.get("/")
def root():
    return {"message": "Welcome to the Drone LiDAR Analysis Platform API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
