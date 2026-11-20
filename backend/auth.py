"""Local demo identity and server-enforced roles."""

import hashlib
import time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from . import storage

ROLES = {
    "ba": "Business Analyst",
    "compliance": "Compliance Officer",
    "pm": "Project Manager",
    "developer": "Software Developer",
}
bearer = HTTPBearer(auto_error=False)


def user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Select a demo role to start a session.")
    digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    with storage.connect() as conn:
        row = conn.execute("SELECT role, expires FROM sessions WHERE token_hash=?", (digest,)).fetchone()
    if not row or row["expires"] <= time.time():
        raise HTTPException(401, "Session expired or invalid. Start a new demo session.")
    return dict(id="demo-" + row["role"], role=row["role"], name=ROLES[row["role"]], token_hash=digest)


def allowed(*roles):
    def dependency(current=Depends(user)):
        if current["role"] not in roles:
            raise HTTPException(403, "This action requires " + " or ".join(ROLES[r] for r in roles) + ".")
        return current

    return dependency
