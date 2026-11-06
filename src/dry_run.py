import random
import time
import uuid
from typing import Any

from src.validator import AccountModel


class DryRunSimulator:
    """Simulador de la PVWA REST API para ejecuciones en modo dry run.

    No contacta con CyberArk ni requiere credenciales. Genera respuestas
    con la misma forma que devuelve la API real al crear una cuenta, de
    modo que el resto del pipeline (informes, resumen CLI) funcione igual.
    """

    def __init__(self, min_latency: float = 0.01, max_latency: float = 0.05) -> None:
        # Rango de latencia simulada para imitar el coste de red real.
        self._min_latency = min_latency
        self._max_latency = max_latency

    def simulate_account(self, account: AccountModel) -> dict[str, Any]:
        """Devuelve una respuesta simulada de éxito para una cuenta."""
        # Pequeña espera aleatoria para que el progreso de la CLI sea realista.
        time.sleep(random.uniform(self._min_latency, self._max_latency))
        return {
            "id": str(uuid.uuid4()),
            "name": account.name,
            "address": account.address,
            "userName": account.username,
            "platformId": account.platform_id,
            "safeName": account.safe_name,
            "secretType": account.secret_type,
            "simulated": True,
        }

    def simulate_all(self, accounts: list[AccountModel]) -> list[dict[str, Any]]:
        """Simula la creación de todas las cuentas recibidas."""
        return [self.simulate_account(account) for account in accounts]
