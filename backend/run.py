#!/usr/bin/env python3
"""
Warehouse Management System - FastAPI Backend
Run this script to start the development server
"""

import uvicorn
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True
    )
