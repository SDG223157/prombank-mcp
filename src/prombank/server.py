"""FastAPI server runner."""

import uvicorn
from .config import settings


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "prombank.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    run_server()