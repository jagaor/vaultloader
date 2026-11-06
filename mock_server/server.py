"""Mock server FastAPI que simula la PVWA REST API v2 de CyberArk.

Permite probar VaultLoader en local sin necesidad de una licencia real.
Los endpoints replican el comportamiento mínimo esperado por CyberArkClient.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

# Credenciales y token fijos para la demo del mock
MOCK_USERNAME = "mockuser"
MOCK_PASSWORD = "MockPass1!"
MOCK_TOKEN = "mock-token-abc123"

app = FastAPI(title="Mock PVWA", version="mock-pvwa-1.0")


class LogonRequest(BaseModel):
    """Cuerpo esperado en el endpoint de logon."""

    username: str
    password: str


class AccountPayload(BaseModel):
    """Cuerpo mínimo para crear una cuenta privilegiada."""

    username: str
    address: str
    platform_id: str = Field(alias="platformId")
    safe_name: str = Field(alias="safeName")
    secret_type: str = Field(alias="secretType")

    model_config = {"populate_by_name": True}


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de vida del mock."""
    return {"status": "ok", "version": "mock-pvwa-1.0"}


@app.post("/PasswordVault/API/auth/Cyberark/Logon")
def logon(payload: LogonRequest) -> str:
    """Valida credenciales y devuelve un token simulado."""
    if payload.username != MOCK_USERNAME or payload.password != MOCK_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return MOCK_TOKEN


@app.post("/PasswordVault/API/Accounts", status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountPayload,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Crea una cuenta simulada y devuelve el objeto con id UUID4."""
    if authorization != MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    account_id = str(uuid.uuid4())
    return {
        "id": account_id,
        "username": payload.username,
        "address": payload.address,
        "platformId": payload.platform_id,
        "safeName": payload.safe_name,
        "secretType": payload.secret_type,
    }


@app.post("/PasswordVault/API/Auth/Logoff", status_code=status.HTTP_200_OK)
def logoff() -> None:
    """Cierra la sesión simulada (no-op)."""
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
