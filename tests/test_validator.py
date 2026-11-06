import pytest

from src.validator import AccountModel, AccountValidator


def _registro_valido(**overrides):
    """Construye un registro mínimo válido y aplica overrides opcionales."""
    base = {
        "username": "svc_backup",
        "address": "10.0.0.5",
        "platform_id": "UnixSSH",
        "safe_name": "SAFE_PROD",
        "secret_type": "password",
    }
    base.update(overrides)
    return base


def test_valid_account():
    """Un registro completo y correcto debe validar sin errores."""
    validator = AccountValidator()
    validos, errores = validator.validate_all([_registro_valido()])
    assert len(validos) == 1
    assert len(errores) == 0
    assert isinstance(validos[0], AccountModel)


def test_missing_platform_id():
    """platform_id vacío debe rechazarse con un error descriptivo."""
    validator = AccountValidator()
    validos, errores = validator.validate_all([_registro_valido(platform_id="")])
    assert len(validos) == 0
    assert len(errores) == 1
    assert "platform_id" in errores[0].message.lower()


def test_username_too_long():
    """Un username de 129 caracteres supera el límite permitido."""
    validator = AccountValidator()
    validos, errores = validator.validate_all([_registro_valido(username="u" * 129)])
    assert len(validos) == 0
    assert len(errores) == 1
    assert "username" in errores[0].message.lower()


def test_invalid_secret_type():
    """secret_type fuera del Literal permitido debe fallar la validación."""
    validator = AccountValidator()
    validos, errores = validator.validate_all([_registro_valido(secret_type="token")])
    assert len(validos) == 0
    assert len(errores) == 1
    assert "secret_type" in errores[0].message.lower()


def test_validate_all_mixed():
    """Con 2 válidos y 1 inválido, los conteos deben reflejarlo."""
    validator = AccountValidator()
    registros = [
        _registro_valido(username="svc_a"),
        _registro_valido(username="svc_b"),
        _registro_valido(username="svc_c", platform_id=""),
    ]
    validos, errores = validator.validate_all(registros)
    assert len(validos) == 2
    assert len(errores) == 1
    assert errores[0].row_index == 2


def test_valid_optional_fields():
    """Los campos opcionales port y extra_pass1 deben parsearse correctamente."""
    validator = AccountValidator()
    registro = _registro_valido(port=22, extra_pass1="abc")
    validos, errores = validator.validate_all([registro])
    assert len(errores) == 0
    assert len(validos) == 1
    assert validos[0].port == 22
    assert validos[0].extra_pass1 == "abc"
