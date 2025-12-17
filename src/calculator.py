import json
import datetime
from datetime import timedelta

def load_rules(path="data/rules.json"):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def calculate_deadline(framework, discovery_date_str, severity):
    rules = load_rules()
    
    if framework not in rules:
        return f"❌ Framework '{framework}' not found. Available: {list(rules.keys())}"
    
    rule = rules[framework]
    discovery_date = datetime.datetime.strptime(discovery_date_str, "%Y-%m-%d")
    
    # 1. Output Header
    output = f"\n🔍 ANALYSIS: {framework} ({rule['jurisdiction']})\n"
    output += f"   Trigger: {rule['trigger']}\n"
    
    # 2. Logic: Hard Hours (GDPR)
    if "deadline_hours" in rule:
        deadline = discovery_date + timedelta(hours=rule['deadline_hours'])
        output += f"🚨 DEADLINE: {deadline.strftime('%Y-%m-%d %H:%M')} ({rule['deadline_hours']} hours from trigger)"

    # 3. Logic: Hard Days (HIPAA)
    elif "deadline_days" in rule:
        deadline = discovery_date + timedelta(days=rule['deadline_days'])
        output += f"📅 DEADLINE: {deadline.strftime('%Y-%m-%d')} ({rule['deadline_days']} days from trigger)"

    # 4. Logic: Business Days (SEC) - Simplified approximation
    elif "deadline_business_days" in rule:
        # Simple logic: Add (days + 2 weekends) roughly
        days_to_add = rule['deadline_business_days'] + 2 
        deadline = discovery_date + timedelta(days=days_to_add)
        output += f"📉 DEADLINE: ~{deadline.strftime('%Y-%m-%d')} ({rule['deadline_business_days']} Business Days)\n"
        output += "   *Note: Verify exact business/holiday calendar."

    # 5. Logic: Qualitative (CCPA, GLBA, SOX)
    elif "deadline_desc" in rule:
        output += f"⚡ DEADLINE: {rule['deadline_desc']}"

    # 6. Notes
    if "note" in rule:
        output += f"\n   📝 Action: {rule['note']}"

    return output

if __name__ == "__main__":
    # Test Suite
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    print(calculate_deadline("SEC_Material_Breach", today, "high"))
    print(calculate_deadline("HIPAA_HITECH", today, "medium"))
    print(calculate_deadline("CCPA_CPRA", today, "medium"))
