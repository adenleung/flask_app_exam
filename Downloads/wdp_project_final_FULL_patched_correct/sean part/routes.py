import os
from flask import Blueprint, send_from_directory

routes_bp = Blueprint("routes_bp", __name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@routes_bp.get("/")
def home():
    return send_from_directory(ROOT_DIR, "index.html")

@routes_bp.get("/<path:filename>")
def pages(filename):
    return send_from_directory(ROOT_DIR, filename)
