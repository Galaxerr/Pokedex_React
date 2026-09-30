"""Minimal application entrypoint; domain routes are intentionally deferred."""

from fastapi import FastAPI

app = FastAPI(title="Pokedex API", version="0.1.0")
