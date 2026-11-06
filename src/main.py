#!/usr/bin/env python3
"""Punto de entrada CLI de VaultLoader.

Orquesta el flujo completo: parseo CSV, validación, onboarding (real o dry-run)
y generación de informes.
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from csv_parser import CSVParser
from validator import AccountValidator
from dry_run import DryRunSimulator
from cyberark_client import CyberArkClient
from report_builder import ReportBuilder

console = Console()


def parse_args() -> argparse.Namespace:
    """Define y parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="VaultLoader: onboarding masivo de cuentas privilegiadas a CyberArk"
    )
    parser.add_argument("--csv", required=True, help="Ruta al fichero CSV de entrada")
    parser.add_argument(
        "--pvwa-url",
        default=os.environ.get("PVWA_URL"),
        help="URL base de la PVWA (por defecto variable de entorno PVWA_URL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simula el onboarding sin contactar la API real",
    )
    parser.add_argument(
        "--report-out",
        default="./reports",
        help="Directorio de salida para los informes (por defecto ./reports)",
    )
    parser.add_argument(
        "--safe",
        default=None,
        help="Safe de destino que sobrescribe el valor del CSV",
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        default=False,
        help="Deshabilita la verificación TLS",
    )
    return parser.parse_args()


async def run_onboarding(
    records: list[dict],
    args: argparse.Namespace,
    console: Console,
) -> list[dict]:
    """Ejecuta el onboarding (real o simulado) con barra de progreso."""
    results: list[dict] = []

    if args.dry_run:
        simulator = DryRunSimulator()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Simulando onboarding...", total=len(records))
            for rec in records:
                res = simulator.simulate(rec)
                results.append(res)
                progress.advance(task)
    else:
        if not args.pvwa_url:
            console.print("[red]Error: se requiere --pvwa-url o la variable PVWA_URL[/red]")
            sys.exit(1)
        client = CyberArkClient(
            base_url=args.pvwa_url,
            verify_ssl=not args.no_ssl_verify,
        )
        await client.authenticate()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Creando cuentas en CyberArk...", total=len(records))
            for rec in records:
                res = await client.create_account(rec)
                results.append(res)
                progress.advance(task)

    return results


def print_summary(
    total: int,
    valid: int,
    schema_errors: int,
    onboarded: int,
    api_errors: int,
    duration: float,
) -> None:
    """Imprime una tabla resumen con los totales del proceso."""
    table = Table(title="Resumen de VaultLoader")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", justify="right")
    table.add_row("Filas procesadas", str(total))
    table.add_row("Válidas (schema)", str(valid))
    table.add_row("Errores de schema", str(schema_errors))
    table.add_row("Onboarded correctamente", str(onboarded))
    table.add_row("Fallidas en API", str(api_errors))
    table.add_row("Duración (s)", f"{duration:.2f}")
    console.print(table)


def main() -> None:
    """Función principal que orquesta todo el flujo."""
    args = parse_args()
    start = time.perf_counter()

    # 1. Parseo del CSV
    console.print(f"[bold]Leyendo CSV:[/bold] {args.csv}")
    parser = CSVParser(args.csv)
    raw_records = parser.parse()
    total = len(raw_records)

    # 2. Validación de registros
    validator = AccountValidator()
    valid_records, schema_errors = validator.validate(raw_records)

    # 3. Mostrar errores de schema si los hay
    if schema_errors:
        err_table = Table(title="Errores de validación de schema")
        err_table.add_column("Fila", style="yellow")
        err_table.add_column("Campo", style="red")
        err_table.add_column("Mensaje")
        for err in schema_errors:
            err_table.add_row(str(err.get("row", "?")), err.get("field", ""), err.get("message", ""))
        console.print(err_table)

    # 4. Sobrescribir Safe si se indicó
    if args.safe:
        for rec in valid_records:
            rec["safe_name"] = args.safe

    # 5. Ejecutar onboarding/simulación
    results = asyncio.run(run_onboarding(valid_records, args, console))

    # 6. Generar informes
    report_builder = ReportBuilder(output_dir=args.report_out)
    report_builder.build(results, schema_errors, total)

    # 7. Resumen final
    onboarded = sum(1 for r in results if r.get("status") == "success")
    api_errors = sum(1 for r in results if r.get("status") == "error")
    duration = time.perf_counter() - start
    print_summary(total, len(valid_records), len(schema_errors), onboarded, api_errors, duration)


if __name__ == "__main__":
    main()