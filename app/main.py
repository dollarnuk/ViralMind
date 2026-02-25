from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from app.api.v1 import endpoints
from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="ViralMind API",
    description="Automated Viral Shorts Generator",
    version="0.1.0",
)

# Mount static files for the Apple-like UI
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static/output", StaticFiles(directory=settings.OUTPUT_DIR), name="output")

# Include API routers
app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to ViralMind API. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
