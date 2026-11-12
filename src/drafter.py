"""Turns the results into HTML files: one report and one draft letter."""
import os
from datetime import date

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


class DraftingEngine:
    def __init__(self, template_dir=TEMPLATE_DIR):
        # autoescape: text from the incident file can never become live HTML.
        self.env = Environment(loader=FileSystemLoader(template_dir),
                               autoescape=select_autoescape(["html"]))

    def _write(self, template_name, context, out_dir, filename):
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.env.get_template(template_name).render(context))
        return path

    def write_report(self, incident, obligations, meta, out_dir="output", today=None):
        """Writes the deadline report and returns its path."""
        today = today or date.today()
        dated = [o for o in obligations if o["due"]]
        context = {
            "incident": incident,
            "meta": meta,
            "today": today,
            "dated": dated,
            "undated": [o for o in obligations if not o["due"] and o["status"] == "Required"],
            "review": [o for o in obligations if o["status"] == "Review"],
            "info": [o for o in obligations if o["status"] == "Not yet in effect"],
            "first": dated[0] if dated else None,
        }
        return self._write("report.html", context, out_dir, "report.html")

    def draft_consumer_notice(self, incident, out_dir="output", meta=None, today=None):
        """Writes a draft letter to affected individuals and returns its path."""
        today = today or date.today()
        labels = (meta or {}).get("data_types", {})
        context = {
            "company_name": incident.get("company_name", "[COMPANY NAME]"),
            "company_address": incident.get("address", "[ADDRESS]"),
            "company_city_state_zip": incident.get("city_state", "[CITY, STATE, ZIP]"),
            "today_date": today.strftime("%B %d, %Y"),
            "discovery_date": incident.get("discovery_date", incident.get("timestamp", "[DISCOVERY DATE]")),
            "breach_date": incident.get("breach_date", "[DATE OF BREACH]"),
            "data_types": [labels.get(t, t.replace("_", " ").title()) for t in incident.get("data_types", [])],
            "hotline_number": incident.get("hotline", "[PHONE NUMBER]"),
        }
        return self._write("us_consumer_notice.html", context, out_dir, "draft_consumer_notice.html")
