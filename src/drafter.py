import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from rich.console import Console

console = Console()

class DraftingEngine:
    def __init__(self, template_dir="templates"):
        # Ensure template dir exists
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
            console.print(f"[yellow]⚠️  Created missing template directory: {template_dir}[/yellow]")

        self.env = Environment(loader=FileSystemLoader(template_dir))

    def draft_consumer_notice(self, incident, obligation):
        """
        Generates an HTML draft for a specific jurisdiction obligation.
        """
        try:
            template = self.env.get_template("us_consumer_notice.html")
        except Exception as e:
            console.print(f"[red]❌ Template Error: Could not load 'us_consumer_notice.html'. {e}[/red]")
            return None

        # Prepare Context Data
        context = {
            "company_name": incident.get("company_name", "[COMPANY NAME]"),
            "company_address": incident.get("address", "[ADDRESS]"),
            "company_city_state_zip": incident.get("city_state", "[CITY, STATE, ZIP]"),
            "today_date": datetime.now().strftime("%B %d, %Y"),
            "discovery_date": incident.get("timestamp", "Unknown Date"),
            "breach_date": incident.get("breach_date", "Unknown Date"),
            "data_types": incident.get("data_types", []),
            "regulator_name": obligation.get("regulator", "the Attorney General"),
            "jurisdiction": obligation.get("jurisdiction", "State"),
            "hotline_number": incident.get("hotline", "1-800-XXX-XXXX")
        }

        # Render
        rendered_html = template.render(context)
        
        # Save File
        filename = f"draft_notice_{obligation['jurisdiction']}_{datetime.now().strftime('%Y%m%d')}.html"
        with open(filename, "w") as f:
            f.write(rendered_html)
            
        console.print(f"[green]📝 Generated Draft:[/green] {filename}")
        return filename
