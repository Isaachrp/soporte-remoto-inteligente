"""ASGI entry point for the central-only delivery application."""
from server.app.main import create_app as base_app


def create_app():
    return base_app(central_only=True)
