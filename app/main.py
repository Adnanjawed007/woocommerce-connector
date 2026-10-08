"""Main entry point for the WooCommerce Connector."""

import uvicorn
from app.mcp.server import app
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.mcp.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )