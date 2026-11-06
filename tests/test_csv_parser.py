import csv

import pytest

from src.csv_parser import CSVParser, ParseError


REQUIRED_COLUMNS = ["username", "address", "platform_id", "safe_name", "secret_type"]


def _write_csv(path, header, rows):
    """Escribe un CSV temporal con la cabecera y filas indicadas."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def test_parse_valid_csv(tmp_path):
    """Un CSV válido devuelve dos dicts con el número de fila CSV correcto."""
    csv_file = tmp_path / "accounts.csv"
    _write_csv(
        csv_file,
        REQUIRED_COLUMNS,
        [
            ["svc_backup", "10.0.0.5", "UnixSSH", "Safes_Backup", "password"],
            ["svc_db", "10.0.0.6", "WinServerLocal", "Safes_DB", "password"],
        ],
    )
    records = CSVParser().parse(str(csv_file))
    assert len(records) == 2
    assert records[0]["_row_number"] == 2
    assert records[1]["_row_number"] == 3
    assert records[0]["username"] == "svc_backup"


def test_missing_column_raises(tmp_path):
    """Si falta una columna obligatoria se lanza ParseError."""
    csv_file = tmp_path / "missing.csv"
    header = ["username", "address", "safe_name", "secret_type"]
    _write_csv(csv_file, header, [["svc_x", "10.0.0.7", "Safes_X", "password"]])
    with pytest.raises(ParseError):
        CSVParser().parse(str(csv_file))


def test_nan_becomes_none(tmp_path):
    """Una celda vacía en un campo opcional se convierte en None."""
    csv_file = tmp_path / "optional.csv"
    header = REQUIRED_COLUMNS + ["description"]
    _write_csv(
        csv_file,
        header,
        [["svc_app", "10.0.0.8", "UnixSSH", "Safes_App", "password", ""]],
    )
    records = CSVParser().parse(str(csv_file))
    assert records[0]["description"] is None


def test_column_normalization(tmp_path):
    """Los nombres de columna se normalizan (minúsculas y sin espacios)."""
    csv_file = tmp_path / "normalized.csv"
    header = ["username", "address", "Platform ID ", "safe_name", "secret_type"]
    _write_csv(
        csv_file,
        header,
        [["svc_norm", "10.0.0.9", "UnixSSH", "Safes_Norm", "password"]],
    )
    records = CSVParser().parse(str(csv_file))
    assert "platform_id" in records[0]
    assert records[0]["platform_id"] == "UnixSSH"
