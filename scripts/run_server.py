#!/usr/bin/env python3
"""
EVO-TR Web Server Runner

Starts the FastAPI server with uvicorn.
"""

import uvicorn
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run the web server."""
    print("🚀 Starting EVO-TR Web Server...")
    print("📍 API Docs: http://localhost:8000/docs")
    print("💬 Chat UI:  http://localhost:8000")
    print("-" * 40)
    
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )


if __name__ == "__main__":
    main()
