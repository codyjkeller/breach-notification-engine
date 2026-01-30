import json
import datetime
import argparse
from datetime import timedelta

# --- 1. CONFIGURATION ---
def load_rules(path="data/rules.json"):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"CRITICAL: Configuration file not found at {path}. Check deployment.")

# --- 2. CORE LOGIC (Returns Data, doesn't print) ---
def calculate_deadline_data(framework, discovery_date_str):
    rules = load_rules()
    
    if framework not in rules:
        return {"error": f"Framework '{framework}' not found. Available: {list(rules.keys())}"}
    
    rule = rules[framework]
    discovery_date = datetime.datetime.strptime(discovery_date_str, "%Y-%m-%d")
    
    # Base Result Object
    result = {
        "framework": framework,
        "jurisdiction": rule['jurisdiction'],
        "trigger_event": rule['trigger'],
        "discovery_date": discovery_date_str,
        "severity_threshold": rule.get('severity_threshold', 'N/A')
    }

    # Logic: Hours
    if "deadline_hours" in rule:
        deadline = discovery_date + timedelta(hours=rule['deadline_hours'])
        result["deadline_iso"] = deadline.isoformat()
        result["deadline_human"] = f"{rule['deadline_hours']} hours from discovery"
        result["is_hard_deadline"] = True

    # Logic: Days
    elif "deadline_days" in rule:
        deadline = discovery_date + timedelta(days=rule['deadline_days'])
        result["deadline_iso"] = deadline.date().isoformat()
        result["deadline_human"] = f"{rule['deadline_days']} days from discovery"
        result["is_hard_deadline"] = True

    # Logic: Business Days (Approximation)
    elif "deadline_business_days" in rule:
        # Adding calendar days as a rough buffer for business days
        # (Real prod code would use pandas.tseries.offsets.BusinessDay)
        days_buffer = rule['deadline_business_days'] + 2 
        deadline = discovery_date + timedelta(days=days_buffer)
        result["deadline_iso"] = deadline.date().isoformat()
        result["deadline_human"] = f"~{rule['deadline_business_days']} Business Days (Verify Calendar)"
        result["is_hard_deadline"] = True

    # Logic: Qualitative
    elif "deadline_desc" in rule:
        result["deadline_iso"] = None
        result["deadline_human"] = rule['deadline_desc']
        result["is_hard_deadline"] = False

    return result

# --- 3. CLI INTERFACE ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate regulatory breach notification deadlines.")
    parser.add_argument("framework", help="The regulation ID (e.g., GDPR, HIPAA_HITECH)")
    parser.add_argument("date", help="Discovery Date (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON for integrations")
    
    args = parser.parse_args()
    
    # Run Logic
    data = calculate_deadline_data(args.framework, args.date)
    
    # Output Router
    if args.json:
        # 🤖 Machine Output
        print(json.dumps(data, indent=2))
    else:
        # 👤 Human Output
        if "error" in data:
            print(f"❌ {data['error']}")
        else:
            print(f"\n🔍 REPORT: {data['framework']}")
            print(f"   📅 Deadline: {data['deadline_human']}")
            if data['deadline_iso']:
                print(f"   ⏰ ISO Timestamp: {data['deadline_iso']}")
            print(f"   ⚖️  Jurisdiction: {data['jurisdiction']}")
