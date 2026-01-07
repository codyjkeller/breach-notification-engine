import json
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

console = Console()

# 🇺🇸 States that follow the "Standard" Notification Rule (Without Unreasonable Delay)
# This maps specific input locations to the "Generic State Breach Statute" in your JSON.
STANDARD_US_STATES = [
    "Alaska", "Arkansas", "District of Columbia", "Georgia", "Hawaii", 
    "Idaho", "Indiana", "Iowa", "Kansas", "Kentucky", "Michigan", 
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", 
    "Nevada", "New Hampshire", "New Jersey", "North Carolina", 
    "North Dakota", "Oklahoma", "Pennsylvania", "South Carolina", 
    "Utah", "Virginia", "West Virginia", "Wyoming"
]

class ComplianceEngine:
    def __init__(self, regulations_path="config/regulations.json"):
        self.regulations = self._load_regulations(regulations_path)

    def _load_regulations(self, path):
        """Safely loads the JSON database from multiple potential locations."""
        if not os.path.exists(path):
            # Fallback for running from root
            path = "config/regulations.json"
            if not os.path.exists(path):
                 # Fallback for running inside src/
                path = "../config/regulations.json"
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data['regulations']
        except FileNotFoundError:
            console.print(f"[red]Error: Could not find regulations.json at {path}[/red]")
            return []

    def assess_incident(self, incident):
        """
        Matches incident data & location to specific laws.
        Returns a list of 'Obligations'.
        """
        obligations = []
        affected_locations = incident.get('affected_locations', [])
        stolen_data = incident.get('data_types', [])
        incident_time = datetime.fromisoformat(incident['timestamp'])

        console.print(f"\n🔎 Analyzing Incident: [bold]{incident['id']}[/bold]")
        console.print(f"   • Data Types: {', '.join(stolen_data)}")
        console.print(f"   • Locations: {', '.join(affected_locations)}\n")

        for reg in self.regulations:
            is_match = False

            # 1. Jurisdiction Match Logic
            # Direct Match (e.g., "California", "EU")
            if reg['jurisdiction'] in affected_locations:
                is_match = True
            
            # Global Match (e.g., if you had a "Global" policy)
            elif reg['jurisdiction'] == "Global":
                is_match = True

            # Grouped/Standard State Match
            elif reg['name'].startswith("Generic State Breach Statute"):
                # Check if any of the affected locations are in our Standard list
                # AND haven't been caught by a specific rule yet.
                for loc in affected_locations:
                    if loc in STANDARD_US_STATES:
                        is_match = True
                        # We tag the specific state so the report is accurate
                        reg['jurisdiction'] = loc 

            if is_match:
                # 2. Data Match (Does the law care about this data?)
                relevant_data = set(stolen_data).intersection(set(reg['trigger_data']))
                
                # Some laws trigger on "All" data or specific fields
                if relevant_data or "all" in reg.get('trigger_data', []):
                    
                    # 3. Calculate Deadline
                    if reg.get('deadline_hours', 0) > 0:
                        deadline_dt = incident_time + timedelta(hours=reg['deadline_hours'])
                        deadline_str = deadline_dt.strftime("%Y-%m-%d %H:%M")
                        
                        # Determine Urgency
                        time_remaining = deadline_dt - datetime.now()
                        is_urgent = time_remaining.total_seconds() < 86400 # Less than 24h
                    else:
                        deadline_str = reg.get('deadline_description', "Asap")
                        is_urgent = True # "ASAP" is always urgent

                    obligations.append({
                        "regulation": reg['name'],
                        "jurisdiction": reg['jurisdiction'], # Uses the specific state name
                        "regulator": reg['authority'],
                        "deadline": deadline_str,
                        "urgent": is_urgent,
                        "triggered_by": list(relevant_data)
                    })

        return obligations

    def generate_report(self, obligations):
        if not obligations:
            console.print("[green]✅ No regulatory notification obligations found.[/green]")
            return

        table = Table(title="⚖️  Legal Breach Obligations", header_style="bold magenta")
        table.add_column("Jurisdiction", style="cyan")
        table.add_column("Regulator", style="white")
        table.add_column("Notification Deadline", style="bold red")
        table.add_column("Trigger Data", style="dim")

        for ob in obligations:
            deadline_display = ob['deadline']
            if ob['urgent']:
                deadline_display = f"🚨 {deadline_display}"
            
            table.add_row(
                ob['jurisdiction'],
                ob['regulator'],
                deadline_display,
                ", ".join(ob['triggered_by'])
            )

        console.print(table)
