"""
FastAPI application for the Railway Traffic Controller Environment.

This module creates an HTTP server that exposes the RailwayControllerEnvironment
over HTTP and WebSocket endpoints.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

from server.railway_environment import RailwayControllerEnvironment


# Create the app with web interface
app = create_app(
    RailwayControllerEnvironment,
    CallToolAction,
    CallToolObservation,
    env_name="railway_controller"
)


@app.get("/")
def root():
    """Root endpoint — shows API info for judges/visitors."""
    return {
        "name": "Railway Traffic Controller",
        "description": "A real-world simulation of railway traffic control for OpenEnv",
        "status": "running",
        "tasks": [
            {"name": "basic_control", "difficulty": "easy", "trains": 2},
            {"name": "junction_management", "difficulty": "medium", "trains": 4},
            {"name": "express_priority", "difficulty": "medium-hard", "trains": 5},
            {"name": "rush_hour", "difficulty": "hard", "trains": 6},
        ],
        "endpoints": {
            "health": "GET /health",
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state",
        },
        "tools": [
            "set_signal", "hold_train", "release_train", "route_train",
            "get_status", "get_collision_warnings", "get_segment_occupancy",
            "get_control_suggestions", "get_delay_status",
        ],
    }


def main():
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()