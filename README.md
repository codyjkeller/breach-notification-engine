# Automated Breach Notification Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Compliance](https://img.shields.io/badge/Compliance-GDPR_&_50_States-red)
![Automation](https://img.shields.io/badge/Automation-Jinja2_Templates-green)

**A programmable legal orchestrator that calculates regulatory deadlines and auto-drafts breach notifications based on jurisdiction (GDPR, CCPA, NY SHIELD, etc.).**

Managing a data breach is a race against the clock. Different laws trigger different deadlines:
* **GDPR:** 72 hours.
* **Puerto Rico:** 10 days.
* **Florida:** 30 days.
* **California:** "Without unreasonable delay."

This engine eliminates the guesswork. It ingests an incident payload, queries a JSON database of **50+ US State & International laws**, and instantly generates the required legal artifacts.

## Key Features

* **Multi-Jurisdictional Logic:** Includes a regulations.json database covering **GDPR** and **all 50 US States** (plus DC/Puerto Rico).
* **Deadline Calculator:** Automatically calculates the exact date/time you must notify regulators based on the incident timestamp and urgency.
* **Auto-Drafting Engine:** Uses **Jinja2** templates to generate formatted HTML notification letters tailored to the specific regulator (e.g., "To the California Attorney General") and incident details.
* **Context-Aware:** Distinguishes between "Consumer Notice" vs. "Regulator Notice" and filters based on trigger data (e.g., "Medical" data triggers HIPAA/State Health laws; "SSN" triggers State AGs).

## Architecture

```mermaid
graph TD
    A[Incident Payload] --> B{Compliance Engine}
    C[Regulations.json] --> B
    
    B -->|Match Location| D{Determine Jurisdiction}
    B -->|Match Data Type| E{Determine Triggers}
    
    D & E --> F[Calculate Deadlines]
    F --> G[Generate CLI Report]
    
    G --> H{Drafting Engine}
    H -->|Load Template| I[Jinja2 Template]
    I --> J[Final HTML Notification Letters]
