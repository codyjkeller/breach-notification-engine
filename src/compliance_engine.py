import json
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

console = Console()

class ComplianceEngine:
    def __init__(self, regulations_path="config/regulations.json"):
        self.regulations = self._load_regulations(regulations_path)

    def _load_regulations(self, path):
        """Safely loads the JSON database."""
        # Handle running from root vs src/
        if not os.path.exists(path):
            fallback = "../config/regulations.json"
            if os.path.exists(fallback):
                path = fallback
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data['regulations']
        except FileNotFoundError:
            console.print(f"[bold red]CRITICAL ERROR: Could not find regulations database at {path}[/bold red]")
            return []

    def assess_incident(self, incident):
        """
        Matches incident data & location to specific laws.
        Now purely dynamic—no hardcoded state lists.
        """
        obligations = []
        affected_locations = incident.get('affected_locations', [])
        stolen_data = incident.get('data_types', [])
        
        # Parse timestamp safely
        try:
            incident_time = datetime.fromisoformat(incident['timestamp'])
        except ValueError:
            incident_time = datetime.now()

        console.print(f"\n🔎 Analyzing Incident: [bold cyan]{incident.get('id', 'Unknown')}[/bold cyan]")
        console.print(f"   • Data Types: [dim]{', '.join(stolen_data)}[/dim]")
        console.print(f"   • Locations:  [dim]{', '.join(affected_locations)}[/dim]\n")

        for reg in self.regulations:
            is_match = False

            # 1. Jurisdiction Match Logic
            # Since regulations.json now lists every state explicitly, we just check direct membership.
            if reg['jurisdiction'] in affected_locations:
                is_match = True
            elif reg['jurisdiction'] == "Global": # Catch-all for EU/International if needed
                is_match = True

            if is_match:
                # 2. Data Match (Does the law care about this data?)
                reg_triggers = set(reg.get('trigger_data', []))
                stolen_set = set(stolen_data)
                
                # Check intersection OR "all" wildcard
                relevant_data = stolen_set.intersection(reg_triggers)
                if relevant_data or "all" in reg_triggers:
                    
                    # 3. Calculate Deadline
                    deadline_str = reg.get('deadline_description', "Asap")
                    is_urgent = False
                    
                    if reg.get('deadline_hours', 0) > 0:
                        deadline_dt = incident_time + timedelta(hours=reg['deadline_hours'])
                        deadline_str = deadline_dt.strftime("%Y-%m-%d %H:%M")
                        
                        # Determine Urgency (< 24h remaining)
                        time_remaining = deadline_dt - datetime.now()
                        if time_remaining.total_seconds() < 86400:
                            is_urgent = True

                    obligations.append({
                        "regulation": reg['name'],
                        "jurisdiction": reg['jurisdiction'],
                        "regulator": reg['authority'],
                        "deadline": deadline_str,
                        "urgent": is_urgent,
                        "triggered_by": list(relevant_data) if relevant_data else ["all"]
                    })

        return obligations

    def generate_report(self, obligations):
        if not obligations:
            console.print("[green]✅ No regulatory notification obligations found.[/green]")
            return

        table = Table(title="⚖️  Legal Breach Obligations", header_style="bold magenta")
        table.add_column("Jurisdiction", style="cyan")
        table.add_column("Regulation", style="dim")
        table.add_column("Deadline", style="bold red")
        table.add_column("Trigger Data", style="white")

        for ob in obligations:
            deadline_display = ob['deadline']
            if ob['urgent']:
                deadline_display = f"🚨 {deadline_display}"
            
            table.add_row(
                ob['jurisdiction'],
                ob['regulation'],
                deadline_display,
                ", ".join(ob['triggered_by'])
            )

        console.print(table)
