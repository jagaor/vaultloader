import pytest

from src.dry_run import DryRunSimulator
from src.validator import AccountModel


def _build_account(username: str = "svc_backup", address: str = "10.0.0.5") -> AccountModel:
    """Construye un AccountModel válido para reutilizar en los tests."""
    return AccountModel(
        username=username,
        address=address,
        platform_id="UnixSSH",
        safe_name="SAFE_PRUEBAS",
        secret_type="password",
    )


def test_simulate_account_returns_dict():
    """La simulación de una cuenta debe devolver un dict con las claves esperadas."""
    simulator = DryRunSimulator()
    account = _build_account()

    result = simulator.simulate_account(account)

    assert isinstance(result, dict)
    assert "id" in result
    assert result["simulated"] is True
    assert result["userName"] == account.username
    assert result["safeName"] == account.safe_name


def test_simulate_all_count():
    """simulate_all debe devolver un dict por cada cuenta de entrada, en el mismo orden."""
    simulator = DryRunSimulator()
    accounts = [_build_account(username=f"svc_{i}") for i in range(5)]

    results = simulator.simulate_all(accounts)

    assert isinstance(results, list)
    assert len(results) == 5
    assert all(isinstance(item, dict) for item in results)
    assert [item["userName"] for item in results] == [a.username for a in accounts]


def test_id_is_unique():
    """Cada simulación debe generar un identificador distinto, incluso para la misma cuenta."""
    simulator = DryRunSimulator()
    account = _build_account()

    first = simulator.simulate_account(account)
    second = simulator.simulate_account(account)

    assert first["id"] != second["id"]
