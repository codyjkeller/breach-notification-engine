"""Breach Notification Engine.

    python run.py                      runs the built-in example
    python run.py my_incident.json     runs your incident
    python run.py my_incident.json --open     also opens the report in your browser
"""
import json
import os
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from rich.console import Console  # noqa: E402
from rich.markup import escape  # noqa: E402
from rich.table import Table  # noqa: E402

from compliance_engine import ComplianceEngine, IncidentError  # noqa: E402
from drafter import DraftingEngine  # noqa: E402

EXAMPLE = os.path.join(HERE, "examples", "sample_incident.json")
console = Console()


def describe_due(item):
    if not item["due"]:
        return "No fixed date"
    left = item["days_left"]
    when = "today" if left == 0 else f"{left} days left" if left > 0 else f"{-left} days OVERDUE"
    return f"{item['due'].isoformat()} ({when})"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    incident_path = args[0] if args else EXAMPLE
    if not args:
        console.print("[dim]No incident file given, so this run uses examples/sample_incident.json.[/dim]")

    try:
        with open(incident_path, "r", encoding="utf-8") as f:
            incident = json.load(f)
    except FileNotFoundError:
        console.print(f"[bold red]Cannot find the file:[/bold red] {escape(incident_path)}")
        return 2
    except json.JSONDecodeError as error:
        console.print(f"[bold red]{escape(incident_path)} is not valid JSON:[/bold red] {escape(str(error))}")
        return 2

    engine = ComplianceEngine()
    try:
        obligations = engine.assess_incident(incident)
    except IncidentError as error:
        console.print(f"[bold red]Problem with the incident file:[/bold red] {escape(str(error))}")
        return 2

    table = Table(title=f"Notification deadlines for {escape(str(incident.get('id', 'this incident')))}")
    for column in ("Deadline", "Where", "Notify", "Status"):
        table.add_column(column)
    for item in obligations:
        late = item["days_left"] is not None and item["days_left"] < 0
        soon = item["days_left"] is not None and 0 <= item["days_left"] <= 7
        style = "bold red" if late else "yellow" if soon else None
        table.add_row(describe_due(item), escape(item["jurisdiction"]), escape(item["who"]), item["status"],
                      style=style)
    console.print(table)

    drafter = DraftingEngine()
    out_dir = os.path.join(os.getcwd(), "output")
    report = drafter.write_report(incident, obligations, engine.meta, out_dir)
    letter = drafter.draft_consumer_notice(incident, out_dir, engine.meta)
    console.print(f"Full report:   {report}")
    console.print(f"Draft letter:  {letter}")
    console.print(f"[dim]Law data last updated {engine.meta['last_updated']}. "
                  "This is not legal advice. Confirm every deadline with counsel.[/dim]")
    if "--open" in argv:
        webbrowser.open("file://" + report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
