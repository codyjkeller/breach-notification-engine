"""Works out who must be notified after a data breach, and by when.

The laws live in config/regulations.json. This file only does three things:
  1. reads the incident and the laws,
  2. decides which laws apply,
  3. counts the days to each deadline.
"""
import json
import os
from datetime import date, datetime, timedelta

REQUIRED = "Required"
REVIEW = "Review"
INFO = "Not yet in effect"

DEFAULT_REGULATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "config", "regulations.json")


class IncidentError(ValueError):
    """The incident file is missing something or contains a value that cannot be used."""


def add_days(start, days, business_days=False):
    """Returns the date `days` after `start`. Business days skip Saturdays and Sundays.

    Public holidays are not skipped. Treat business-day dates as the latest
    possible date and confirm them yourself.
    """
    if not business_days:
        return start + timedelta(days=days)
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def parse_date(value, field):
    """Accepts 2026-11-02 or a full timestamp such as 2026-11-02T09:30:00."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).strip()).date()
    except ValueError:
        raise IncidentError(f'"{field}" must be a date written as YYYY-MM-DD, for example 2026-11-02. '
                            f"Got: {value!r}") from None


class ComplianceEngine:
    def __init__(self, regulations_path=DEFAULT_REGULATIONS):
        with open(regulations_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.meta = data["meta"]
        self.states = {s["jurisdiction"].lower(): s for s in data["states"]}
        self.sector_rules = {r["key"]: r for r in data["sector_rules"]}
        self.core_types = set(self.meta["core_data_types"])
        self.known_types = set(self.meta["data_types"])

    # ---- reading the incident -------------------------------------------------

    def read_incident(self, incident):
        """Checks the incident and returns it in one tidy shape."""
        discovered = incident.get("discovery_date", incident.get("timestamp"))
        if not discovered:
            raise IncidentError('The incident needs a "discovery_date" (the day you found out about the breach).')
        discovery_date = parse_date(discovered, "discovery_date")

        data_types = [str(t).strip().lower() for t in incident.get("data_types", [])]
        if not data_types:
            raise IncidentError('The incident needs at least one entry in "data_types".')
        unknown = [t for t in data_types if t not in self.known_types]
        if unknown:
            raise IncidentError(f"Unknown data type(s): {', '.join(unknown)}. "
                                f"Use: {', '.join(sorted(self.known_types))}.")

        # Preferred: {"California": 1200}. Older files used a plain list of names.
        residents = incident.get("affected_residents")
        if residents is None:
            residents = {name: None for name in incident.get("affected_locations", [])}
        if not isinstance(residents, dict):
            raise IncidentError('"affected_residents" must look like {"California": 1200, "Texas": 300}.')
        counts = {}
        for name, count in residents.items():
            if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
                raise IncidentError(f'The number of affected residents for "{name}" must be a whole number.')
            if count != 0:
                counts[str(name).strip()] = count

        sectors = [str(s).strip().lower() for s in incident.get("sectors", [])]
        unknown = [s for s in sectors if s not in self.sector_rules]
        if unknown:
            raise IncidentError(f"Unknown sector(s): {', '.join(unknown)}. "
                                f"Use: {', '.join(sorted(self.sector_rules))}.")
        if not counts and not sectors:
            raise IncidentError('The incident needs "affected_residents", for example {"California": 1200}.')

        return {"discovery_date": discovery_date, "data_types": data_types, "residents": counts, "sectors": sectors}

    # ---- deciding what applies -----------------------------------------------

    def _state_obligations(self, state, count, facts):
        discovery, data_types = facts["discovery_date"], set(facts["data_types"])
        covered = data_types & (self.core_types | set(state["also_covers"]))
        base = {"jurisdiction": state["jurisdiction"], "law": state["law"], "notes": state["notes"]}

        if not covered:
            # Never drop a state silently: say that a person has to decide.
            labels = ", ".join(self.meta["data_types"][t] for t in sorted(data_types))
            return [dict(base, who="Affected individuals", status=REVIEW, due=None,
                         timing=f"This dataset does not list these data types as covered by this law: {labels}. "
                                "Confirm with counsel before deciding that no notice is owed.")]

        days = state["individual_notice_days"]
        individual_due = add_days(discovery, days) if days else None
        results = [dict(base, who="Affected individuals", status=REQUIRED, due=individual_due,
                        timing=state["individual_notice_text"])]

        if state["regulator"]:
            minimum = state["regulator_min_residents"]
            threshold = state["regulator_threshold_text"]
            if count is None and minimum > 1:
                status, timing = REVIEW, (f"Required when: {threshold}. You did not give a number of affected "
                                          f"residents. {state['regulator_timing_text']}")
            elif count is not None and count < minimum:
                return results
            else:
                status, timing = REQUIRED, f"{state['regulator_timing_text']} (Applies when: {threshold}.)"

            due = None
            if state["regulator_days"] is not None:
                if state["regulator_days_counted_from"] == "discovery":
                    due = add_days(discovery, state["regulator_days"], state["regulator_business_days"])
                elif individual_due:
                    # Latest possible date: counted from the last day residents may be notified.
                    due = add_days(individual_due, state["regulator_days"], state["regulator_business_days"])
            results.append(dict(base, who=state["regulator"], status=status, due=due, timing=timing))
        return results

    def _sector_obligations(self, rule, facts, total_affected):
        base = {"jurisdiction": rule["name"], "law": rule["law"], "notes": rule["applies_to"]}
        if rule["status"] != "in_effect":
            return [dict(base, who="-", status=INFO, due=None, timing=rule["status_text"])]
        results = []
        for item in rule["obligations"]:
            if total_affected is not None and total_affected < item["min_affected"]:
                continue
            status = REQUIRED if total_affected is not None or item["min_affected"] <= 1 else REVIEW
            due = add_days(facts["discovery_date"], item["days"], item["business_days"]) if item["days"] else None
            results.append(dict(base, who=item["who"], status=status, due=due, timing=item["text"]))
        return results

    def assess_incident(self, incident, today=None):
        """Returns a list of obligations, soonest deadline first."""
        facts = self.read_incident(incident)
        today = today or date.today()
        obligations = []

        for name, count in facts["residents"].items():
            state = self.states.get(name.lower())
            if state is None:
                obligations.append({"jurisdiction": name, "law": "-", "notes": "", "who": "Unknown", "status": REVIEW,
                                    "due": None, "timing": "This place is not in the dataset. Check the spelling "
                                    "(use full names such as \"New York\"), or ask counsel about its law."})
                continue
            obligations.extend(self._state_obligations(state, count, facts))

        known_counts = [c for c in facts["residents"].values() if c is not None]
        total = sum(known_counts) if len(known_counts) == len(facts["residents"]) and known_counts else None
        for key in facts["sectors"]:
            obligations.extend(self._sector_obligations(self.sector_rules[key], facts, total))

        for item in obligations:
            item["days_left"] = (item["due"] - today).days if item["due"] else None
        # Dated deadlines first (soonest at the top), then the undated ones.
        obligations.sort(key=lambda o: (o["due"] is None, o["due"] or date.max, o["jurisdiction"], o["who"]))
        return obligations
