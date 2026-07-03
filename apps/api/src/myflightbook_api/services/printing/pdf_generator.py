from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Sequence

from myflightbook_api.models.flight import Flight
from myflightbook_api.models.user import User

@dataclass
class PrintOptions:
    include_signatures: bool = True
    include_images: bool = False
    include_map: bool = False
    flights_per_page: int = 15
    page_size: str = "A4" # Letter or A4
    orientation: str = "Landscape" # Portrait or Landscape

class LogbookPDFGenerator:
    """
    Generates a printable PDF logbook from a set of flights.
    """

    def __init__(self, user: User, flights: Sequence[Flight], options: PrintOptions):
        self.user = user
        self.flights = flights
        self.options = options

    def generate_html_template(self) -> str:
        page_summaries = self._calculate_page_subtotals()
        page_size = (self.options.page_size or "A4").strip()
        orientation = (self.options.orientation or "Landscape").strip().lower()
        flights_per_page = max(1, int(self.options.flights_per_page or 15))
        pages = [
            self.flights[index:index + flights_per_page]
            for index in range(0, len(self.flights), flights_per_page)
        ] or [[]]

        page_markup: list[str] = []
        for index, page_flights in enumerate(pages):
            summary = page_summaries[index] if index < len(page_summaries) else {}
            amount_forward = _format_totals(summary, prefix="amount_forward_")
            page_totals = _format_totals(summary)
            rows = "".join(_flight_row_markup(flight) for flight in page_flights) or (
                "<tr><td colspan='10' class='empty'>No flights on this page</td></tr>"
            )
            page_markup.append(
                f"""
                <section class="page">
                  <header class="page-header">
                    <div>
                      <h1>Logbook Summary</h1>
                      <p>{html.escape(getattr(self.user, "display_name", "Unknown Pilot"))}</p>
                    </div>
                    <div class="page-meta">
                      <span>Page {index + 1}</span>
                      <span>{len(page_flights)} flights</span>
                    </div>
                  </header>
                  <table class="carry-forward">
                    <thead>
                      <tr>
                        <th>Amount Forward</th>
                        <th>Total</th>
                        <th>PIC</th>
                        <th>SIC</th>
                        <th>XC</th>
                        <th>Night</th>
                        <th>IMC</th>
                        <th>Landings</th>
                        <th>Approaches</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Prior pages</td>
                        <td>{amount_forward['total_time']}</td>
                        <td>{amount_forward['pic_time']}</td>
                        <td>{amount_forward['sic_time']}</td>
                        <td>{amount_forward['cross_country']}</td>
                        <td>{amount_forward['night']}</td>
                        <td>{amount_forward['imc']}</td>
                        <td>{amount_forward['landings']}</td>
                        <td>{amount_forward['approaches']}</td>
                      </tr>
                    </tbody>
                  </table>
                  <table class="logbook">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Route</th>
                        <th>Total</th>
                        <th>PIC</th>
                        <th>SIC</th>
                        <th>XC</th>
                        <th>Night</th>
                        <th>IMC</th>
                        <th>Landings</th>
                        <th>Approaches</th>
                      </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                    <tfoot>
                      <tr>
                        <th colspan="2">Page Totals</th>
                        <th>{page_totals['total_time']}</th>
                        <th>{page_totals['pic_time']}</th>
                        <th>{page_totals['sic_time']}</th>
                        <th>{page_totals['cross_country']}</th>
                        <th>{page_totals['night']}</th>
                        <th>{page_totals['imc']}</th>
                        <th>{page_totals['landings']}</th>
                        <th>{page_totals['approaches']}</th>
                      </tr>
                    </tfoot>
                  </table>
                </section>
                """
            )

        return f"""
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <style>
              @page {{
                size: {page_size} {"landscape" if orientation == "landscape" else "portrait"};
                margin: 16mm;
              }}
              body {{
                font-family: Arial, Helvetica, sans-serif;
                color: #1f2937;
                margin: 0;
              }}
              .page {{
                page-break-after: always;
              }}
              .page:last-child {{
                page-break-after: auto;
              }}
              .page-header {{
                align-items: baseline;
                display: flex;
                justify-content: space-between;
                margin-bottom: 12px;
              }}
              h1 {{
                font-size: 18px;
                margin: 0 0 4px 0;
              }}
              p, span {{
                font-size: 12px;
                margin: 0;
              }}
              table {{
                border-collapse: collapse;
                margin-bottom: 12px;
                width: 100%;
              }}
              th, td {{
                border: 1px solid #9ca3af;
                font-size: 11px;
                padding: 6px 8px;
                text-align: left;
              }}
              thead th, tfoot th {{
                background: #e5e7eb;
              }}
              .empty {{
                color: #6b7280;
                text-align: center;
              }}
            </style>
          </head>
          <body>
            {''.join(page_markup)}
          </body>
        </html>
        """

    async def render_pdf_to_bytes(self) -> bytes:
        rendered_html = self.generate_html_template()
        try:
            from weasyprint import HTML
        except ImportError:
            return build_basic_pdf(_html_to_text(rendered_html))

        return HTML(string=rendered_html).write_pdf()

    def _calculate_page_subtotals(self) -> list[dict[str, float]]:
        numeric_fields = (
            "total_time",
            "pic_time",
            "sic_time",
            "dual_given",
            "dual_received",
            "cross_country",
            "night",
            "imc",
            "simulated_instrument",
            "landings",
            "full_stop_landings_day",
            "full_stop_landings_night",
            "approaches",
        )
        flights_per_page = max(1, int(self.options.flights_per_page or 15))
        running_totals = {field: 0.0 for field in numeric_fields}
        summaries: list[dict[str, float]] = []

        for start in range(0, len(self.flights), flights_per_page):
            chunk = self.flights[start:start + flights_per_page]
            summary = {f"amount_forward_{field}": running_totals[field] for field in numeric_fields}

            for field in numeric_fields:
                page_total = sum(_as_float(getattr(flight, field, 0.0)) for flight in chunk)
                summary[field] = page_total
                running_totals[field] += page_total

            summaries.append(summary)

        return summaries


def _flight_row_markup(flight: Flight) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(str(getattr(flight, 'flight_date', '')))}</td>"
        f"<td>{html.escape(getattr(flight, 'route', '') or '')}</td>"
        f"<td>{_format_number(getattr(flight, 'total_time', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'pic_time', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'sic_time', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'cross_country', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'night', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'imc', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'landings', 0))}</td>"
        f"<td>{_format_number(getattr(flight, 'approaches', 0))}</td>"
        "</tr>"
    )


def _format_totals(summary: dict[str, float], *, prefix: str = "") -> dict[str, str]:
    return {
        "total_time": _format_number(summary.get(f"{prefix}total_time", 0.0)),
        "pic_time": _format_number(summary.get(f"{prefix}pic_time", 0.0)),
        "sic_time": _format_number(summary.get(f"{prefix}sic_time", 0.0)),
        "cross_country": _format_number(summary.get(f"{prefix}cross_country", 0.0)),
        "night": _format_number(summary.get(f"{prefix}night", 0.0)),
        "imc": _format_number(summary.get(f"{prefix}imc", 0.0)),
        "landings": _format_number(summary.get(f"{prefix}landings", 0.0)),
        "approaches": _format_number(summary.get(f"{prefix}approaches", 0.0)),
    }


def _as_float(value: float | int | object) -> float:
    return float(value or 0.0)


def _format_number(value: float | int | object) -> str:
    numeric = _as_float(value)
    return f"{numeric:.1f}" if numeric.is_integer() else f"{numeric:.2f}"


def _html_to_text(rendered_html: str) -> str:
    stripped = re.sub(r"<[^>]+>", "\n", rendered_html)
    stripped = html.unescape(stripped)
    return "\n".join(line.strip() for line in stripped.splitlines() if line.strip())


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_basic_pdf(text: str) -> bytes:
    lines = [line for line in text.splitlines() if line.strip()] or ["MyFlightbook"]
    usable_lines = lines[:48]
    content_lines = ["BT", "/F1 10 Tf", "48 760 Td"]
    for index, line in enumerate(usable_lines):
        if index == 0:
            content_lines.append(f"({_escape_pdf_text(line[:100])}) Tj")
        else:
            content_lines.append(f"0 -14 Td ({_escape_pdf_text(line[:100])}) Tj")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("utf-8")

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Length " + str(len(content_stream)).encode("ascii") + b" >>\nstream\n" + content_stream + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)
