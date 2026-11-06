from typing import Literal, Optional, Any

from pydantic import BaseModel, Field, ValidationError


class AccountModel(BaseModel):
    """Modelo de cuenta privilegiada compatible con la PVWA REST API v2.

    Los campos obligatorios cubren los requisitos mínimos exigidos por
    CyberArk para crear una cuenta en un Safe. Los campos opcionales
    permiten transportar metadatos adicionales sin romper la validación.
    """

    username: str = Field(..., max_length=128)
    address: str = Field(..., max_length=255)
    platform_id: str = Field(..., min_length=1, max_length=64)
    safe_name: str = Field(..., min_length=1, max_length=50)
    secret_type: Literal["password", "key"]
    secret: str = Field(..., min_length=1)
    name: str = Field(..., max_length=255)

    port: Optional[int] = None
    extra_pass1: Optional[str] = None
    extra_pass2: Optional[str] = None
    extra_pass3: Optional[str] = None


class AccountValidator:
    """Valida registros crudos del CSV contra el esquema de CyberArk.

    Recibe la lista de diccionarios producida por CSVParser y devuelve
    una tupla con los modelos válidos y la lista de errores legibles
    referenciados a su número de fila original.
    """

    def validate_all(
        self, raw_records: list[dict]
    ) -> tuple[list[AccountModel], list[dict[str, Any]]]:
        valid_accounts: list[AccountModel] = []
        invalid_records: list[dict[str, Any]] = []

        for index, raw in enumerate(raw_records):
            # El número de fila visible para el operador empieza en 2
            # (la fila 1 corresponde a la cabecera del CSV).
            row_number = index + 2
            try:
                account = AccountModel(**raw)
            except ValidationError as exc:
                invalid_records.append(
                    self._to_error_dict(exc, raw, row_number)
                )
                continue
            except TypeError as exc:
                # Caso defensivo: claves inesperadas o no serializables.
                invalid_records.append(
                    {
                        "row_number": row_number,
                        "username": str(raw.get("username", "")),
                        "errors": [f"Error de estructura: {exc}"],
                    }
                )
                continue

            valid_accounts.append(account)

        return valid_accounts, invalid_records

    @staticmethod
    def _to_error_dict(
        exc: ValidationError, raw: dict, row_number: int
    ) -> dict[str, Any]:
        """Convierte una ValidationError de Pydantic en un dict legible."""
        messages: list[str] = []
        for err in exc.errors():
            location = ".".join(str(part) for part in err.get("loc", ()))
            message = err.get("msg", "valor inválido")
            if location:
                messages.append(f"{location}: {message}")
            else:
                messages.append(message)

        return {
            "row_number": row_number,
            "username": str(raw.get("username", "")),
            "errors": messages,
        }
