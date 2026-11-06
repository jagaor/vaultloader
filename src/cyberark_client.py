import httpx


class CyberArkAPIError(Exception):
    """Excepción lanzada cuando la API de CyberArk devuelve un error HTTP."""

    def __init__(self, message: str, status_code: int, endpoint: str, body: str):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint
        self.body = body

    def __str__(self) -> str:
        return (
            f"{super().__str__()} "
            f"[status={self.status_code}, endpoint={self.endpoint}, body={self.body}]"
        )


class CyberArkClient:
    """Cliente HTTP para interactuar con la API REST v2 de CyberArk PVWA."""

    def __init__(self, pvwa_url: str, username: str, password: str, verify_ssl: bool = True):
        self.pvwa_url = pvwa_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token: str | None = None

        # Cliente httpx síncrono con timeout de 30 segundos
        self._client = httpx.Client(
            base_url=self.pvwa_url,
            verify=self.verify_ssl,
            timeout=30.0,
        )

    def _handle_response_error(self, response: httpx.Response, endpoint: str) -> None:
        """Lanza CyberArkAPIError si la respuesta contiene un código de error HTTP."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise CyberArkAPIError(
                message=f"Error en la llamada a {endpoint}",
                status_code=exc.response.status_code,
                endpoint=endpoint,
                body=exc.response.text,
            ) from exc

    def authenticate(self) -> str:
        """Autentica contra PVWA y almacena el token de sesión.

        El token se devuelve como cuerpo de la respuesta (texto plano, sin JSON).
        """
        endpoint = "/PasswordVault/API/auth/Cyberark/Logon"
        payload = {"username": self.username, "password": self.password}
        response = self._client.post(endpoint, json=payload)
        self._handle_response_error(response, endpoint)

        # El token es el cuerpo de la respuesta como cadena
        self.token = response.text.strip()
        return self.token

    def create_account(self, account) -> dict:
        """Crea una cuenta privilegiada en el Safe indicado.

        Args:
            account: Instancia de AccountModel (pydantic) con los datos de la cuenta.

        Returns:
            Diccionario con la respuesta de la API.
        """
        if not self.token:
            raise CyberArkAPIError(
                message="No hay token de autenticación. Llame a authenticate() primero.",
                status_code=401,
                endpoint="/PasswordVault/API/Accounts",
                body="",
            )

        endpoint = "/PasswordVault/API/Accounts"
        headers = {"Authorization": self.token}

        # Construir el cuerpo JSON a partir del modelo de cuenta
        body = {
            "name": account.name,
            "address": account.address,
            "userName": account.username,
            "platformId": account.platform_id,
            "safeName": account.safe_name,
            "secretType": account.secret_type,
            "secret": account.secret,
        }

        # Añadir propiedades extra de la plataforma si existen
        if account.platform_account_properties:
            body["platformAccountProperties"] = account.platform_account_properties

        response = self._client.post(endpoint, json=body, headers=headers)
        self._handle_response_error(response, endpoint)
        return response.json()

    def logoff(self) -> None:
        """Cierra la sesión en PVWA."""
        if not self.token:
            return

        endpoint = "/PasswordVault/API/Auth/Logoff"
        headers = {"Authorization": self.token}
        response = self._client.post(endpoint, headers=headers)
        self._handle_response_error(response, endpoint)
        self.token = None

    def close(self) -> None:
        """Cierra el cliente HTTP subyacente."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
