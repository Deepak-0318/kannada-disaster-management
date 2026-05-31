"""
extensions.py — Shared Global Flask Extensions
Kannada Disaster Management AI System
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Globally instantiable rate limiter to avoid circular import issues
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per minute"],
    storage_uri="memory://",
)
