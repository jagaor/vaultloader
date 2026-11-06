import re
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "username",
    "address",
    "platform_id",
    "safe_name",
    "secret_type",
    "secret",
    "name",
]


class ParseError(Exception):
    """Error lanzado cuando el CSV no cumple con el formato esperado."""


class CSVParser:
    """Parser de ficheros CSV para la carga masiva de cuentas en CyberArk.

    Lee un CSV, normaliza los nombres de columna y devuelve una lista de
    diccionarios con los datos crudos, listos para la capa de validación.
    """

    def parse(self, filepath: str) -> list[dict]:
        """Lee y normaliza el CSV indicado.

        Args:
            filepath: Ruta al fichero CSV de entrada.

        Returns:
            Lista de diccionarios, uno por fila, con los nombres de columna
            normalizados y el campo '_row_number' indicando la fila original
            (empezando en 2, ya que la fila 1 es la cabecera).

        Raises:
            ParseError: Si el fichero no existe, está vacío o le faltan
                columnas requeridas.
        """
        path = Path(filepath)
        if not path.is_file():
            raise ParseError(f"El fichero no existe o no es accesible: {filepath}")

        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
        except pd.errors.EmptyDataError as exc:
            raise ParseError(f"El fichero CSV está vacío: {filepath}") from exc
        except pd.errors.ParserError as exc:
            raise ParseError(f"Error al parsear el CSV: {exc}") from exc

        df.columns = [self._normalize_column(col) for col in df.columns]

        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ParseError(
                "Faltan columnas requeridas en el CSV: " + ", ".join(missing)
            )

        df = df.where(pd.notna(df), None)

        records = df.to_dict(orient="records")
        for idx, record in enumerate(records, start=2):
            record["_row_number"] = idx

        return records

    @staticmethod
    def _normalize_column(name: str) -> str:
        """Normaliza el nombre de una columna: minúsculas, sin espacios
        extremos y con espacios internos reemplazados por guiones bajos."""
        normalized = name.strip().lower()
        normalized = re.sub(r"\s+", "_", normalized)
        return normalized
