import pkg_resources

from conda_vendor.conda_vendor import main

__all__ = ["main"]

try:
    __version__ = pkg_resources.get_distribution("conda_vendor").version
except Exception:
    __version__ = "unknown"
