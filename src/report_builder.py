import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


class ReportBuilder:
    """Genera informes HTML y JSON a partir del resumen de ejecución."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        # Crear el directorio de salida si no existe
        os.makedirs(self.output_dir, exist_ok=True)

    def build(self, summary: dict) -> tuple[str, str]:
        """Construye los informes y devuelve las rutas (html, json)."""
        # Generar marca de tiempo para los nombres de fichero
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"vaultloader_{timestamp}"
        json_path = os.path.join(self.output_dir, f"{base_name}.json")
        html_path = os.path.join(self.output_dir, f"{base_name}.html")

        # Serializar el resumen a JSON (default=str para tipos no serializables)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

        # Configurar Jinja2 para cargar la plantilla desde templates/
        env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("report.html.j2")

        # Renderizar la plantilla con el resumen
        html_content = template.render(summary=summary)

        # Guardar el HTML generado
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path, json_path
