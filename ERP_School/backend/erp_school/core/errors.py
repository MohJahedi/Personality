"""core / errors.py: extracted from the real v0.3 pilot."""
from __future__ import annotations


class AppError(Exception):

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status
