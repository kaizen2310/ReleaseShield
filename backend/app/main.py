from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic Software Release Risk Advisor",
    version="0.1.0",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR)
