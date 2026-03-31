"""
renderers/pdf_renderer.py
Generates PDF and HTML preview from CVData using WeasyPrint + Jinja2.
"""
from __future__ import annotations
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from schemas.cv_schema import CVData

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_html_preview(cv: CVData) -> str:
    """Render the CV as an HTML string for in-chat preview."""
    env = _get_jinja_env()
    template_name = f"{cv.selected_template}.html"

    # Fall back to professional template if selected one doesn't exist
    if not (TEMPLATES_DIR / template_name).exists():
        template_name = "professional.html"

    template = env.get_template(template_name)
    return template.render(cv=cv)


def render_pdf(cv: CVData) -> bytes:
    """Render the CV as a PDF binary using WeasyPrint."""
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise ImportError("WeasyPrint is not installed. Run: pip install weasyprint")

    html_string = render_html_preview(cv)
    pdf_bytes = HTML(string=html_string, base_url=str(TEMPLATES_DIR)).write_pdf()
    return pdf_bytes
