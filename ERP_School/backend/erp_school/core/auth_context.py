"""Transport-independent facts needed to authenticate a request."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthContext:
    session_token: str
    remote_address: str
