import importlib.metadata

from conda_vendor.conda_vendor import main

__all__ = ["main"]

try:
    __version__ = importlib.metadata.version("conda_vendor")
except Exception:
    __version__ = "unknown"
