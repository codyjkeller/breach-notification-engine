# Breach Notification Engine

### Who do we have to tell about a data breach, and by when?

![Status](https://img.shields.io/badge/Status-Active-success.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Laws](https://img.shields.io/badge/Law_data-November_2026-purple.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## In one minute

After a data breach, a company may owe notices to affected people and to regulators in every state where those people live. Each state sets its own deadline. Some give 30 days, some 60, some name no number at all, and several changed in 2026.

You tell this tool **when you discovered the breach, what kind of data was involved, and how many people were affected in each state**. It gives you:

- a list of every notice you may owe, **sorted by due date**, with the days remaining,
- a report you can open in any web browser and share with your legal team,
- a draft letter to affected people.

It runs on your own computer. Nothing is sent anywhere.

> **This is a planning aid, not legal advice.** Use it to get organized in the first hours. Have counsel confirm every deadline before you act on it.

---

## Quick start

You need **Python 3.10 or newer**. Check with `python --version` (on a Mac, `python3 --version`). If you don't have it, get it from [python.org/downloads](https://www.python.org/downloads/).

```bash
git clone https://github.com/codyjkeller/breach-notification-engine.git
cd breach-notification-engine
pip install -r requirements.txt
python run.py
```

No git? On the GitHub page choose **Code → Download ZIP**, unzip it, and open a terminal in that folder.

That runs a built-in example and prints something like this (shortened here):

```text
                  Notification deadlines for INC-2026-EXAMPLE
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Deadline                  ┃ Where      ┃ Notify                   ┃ Status   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 2026-11-20 (8 days left)  │ Vermont    │ Vermont Attorney General │ Required │
│ 2026-12-02 (20 days left) │ California │ Affected individuals     │ Required │
│ 2026-12-02 (20 days left) │ New York   │ Affected individuals     │ Required │
│ 2026-12-02 (20 days left) │ Texas      │ Texas Attorney General   │ Required │
│ 2026-12-17 (35 days left) │ California │ California Attorney      │ Required │
│                           │            │ General                  │          │
│ ...                       │            │                          │          │
└───────────────────────────┴────────────┴──────────────────────────┴──────────┘
Full report:   output/report.html
Draft letter:  output/draft_consumer_notice.html
```

Open `output/report.html` in your browser (double-click it), or let the tool open it for you:

```bash
python run.py --open
```

---

## Run it on your own incident

1. Copy `examples/sample_incident.json` and give the copy a name, for example `my_incident.json`.
2. Open it in any text editor and change the values.
3. Run `python run.py my_incident.json --open`

The file looks like this:

```json
{
  "id": "INC-2026-EXAMPLE",
  "company_name": "Example Logistics Inc.",
  "address": "123 Example Way",
  "city_state": "San Francisco, CA 94105",
  "hotline": "1-888-555-0199",

  "discovery_date": "2026-11-02",
  "breach_date": "2026-10-28",

  "data_types": ["ssn", "medical"],

  "affected_residents": {
    "California": 1200,
    "Texas": 300
  },

  "sectors": []
}
```

| Field | What to put |
| :--- | :--- |
| `discovery_date` | The day you found out about the breach, as `YYYY-MM-DD`. All deadlines count from this day. |
| `breach_date` | The day the breach happened. Only used in the draft letter. |
| `data_types` | What was exposed. Pick from the list below. |
| `affected_residents` | Each state's full name and how many of its residents were affected. The number decides whether a regulator must be told. |
| `sectors` | Usually empty: `[]`. Add an entry only if one of the special rules below applies to you. |
| the rest | Your company details, used in the draft letter. |

**Data types**

| Write | Meaning |
| :--- | :--- |
| `ssn` | Social Security number |
| `driver_license` | Driver's license or state ID number |
| `financial` | Bank account or payment card number with an access code or password |
| `medical` | Medical or health insurance information |
| `biometric` | Fingerprint, face or retina scan |
| `credentials` | Username or e-mail address with a password or security answer |
| `other` | Anything else |

**Sectors (optional)**

| Write | Adds |
| :--- | :--- |
| `healthcare` | HIPAA: individuals and HHS within 60 days; media if more than 500 in a state |
| `public_company` | SEC Form 8-K: 4 business days after deciding the incident is material |
| `financial_institution` | FTC Safeguards Rule: FTC within 30 days for 500 or more consumers |
| `eu_residents` | GDPR: data protection authority within 72 hours |
| `critical_infrastructure` | CIRCIA: shown as **not yet in effect** (see below) |

---

## Reading the report

The report has up to four parts:

| Section | Meaning |
| :--- | :--- |
| **Deadlines with a date** | Notices with a fixed number of days, soonest first. Red means overdue; amber means 7 days or less. |
| **Required, with no fixed number of days** | The law says "without unreasonable delay" or similar. Treat these as urgent. |
| **A person needs to review these** | The tool could not decide. Examples: the state's law may not cover that type of data, or you did not give a head count. It never quietly drops a state. |
| **Rules that are not in effect yet** | Shown so you know where they stand. |

Each row names the law, so your counsel can check it quickly.

---

## What the law data covers (November 2026)

All 50 states, the District of Columbia and Puerto Rico, plus the five sector rules above. Changes from 2026 that are included:

| Where | What changed |
| :--- | :--- |
| **California** | SB 446, in effect January 1, 2026: residents must be notified within 30 calendar days. The Attorney General gets a sample notice within 15 days after that when more than 500 residents are notified. |
| **Oklahoma** | SB 626, in effect January 1, 2026: the Attorney General must be told within 60 days of notifying residents when 500 or more are affected. Biometric data is now covered. |
| **Delaware** | HB 381, in effect September 2, 2026: adds a 60-day Attorney General deadline and narrows the exemption for HIPAA- and GLBA-regulated companies. Lawyers disagree on parts of it, so the report tells you to confirm. |
| **District of Columbia** | Law 26-187, in effect September 26, 2026: penalties for violations are now mandatory. Deadlines did not change. |
| **Vermont** | Act 138 of 2026 creates a separate breach regime for data brokers, with related provisions starting January 1, 2027. Not modeled by this tool. |
| **CIRCIA (federal)** | Still not in effect. CISA sent the final rule for White House review on October 1, 2026, and it had not been published as of November 12, 2026. |

Where this information came from is listed under `sources` at the top of `config/regulations.json`. It was compiled from published legal summaries, **not checked line by line against each statute**.

### Keeping it current

All of the law data is in one file, `config/regulations.json`. No code needs to change when a law changes. Each state looks like this:

```json
{
  "jurisdiction": "Texas",
  "law": "Tex. Bus. & Com. Code § 521.053",
  "individual_notice_days": 60,
  "individual_notice_text": "Within 60 days of determining the breach occurred.",
  "regulator": "Texas Attorney General",
  "regulator_min_residents": 250,
  "regulator_threshold_text": "250 or more residents",
  "regulator_days": 30,
  "regulator_days_counted_from": "discovery",
  "regulator_business_days": false,
  "regulator_timing_text": "Within 30 days, using the Attorney General's electronic form.",
  "also_covers": ["medical"],
  "notes": ""
}
```

- Use `null` for `individual_notice_days` or `regulator_days` when the law names no number.
- `regulator_days_counted_from` is `"discovery"` or `"individual_notice"` (days after residents are notified).
- `also_covers` lists data types the law covers beyond Social Security numbers, driver's licenses and financial accounts, which every state covers.
- After editing, update `last_updated` at the top of the file and run `pytest`.

---

## What it does not do

- **Decide whether you had a "breach".** Many laws excuse encrypted data or incidents with no real risk of harm.
- **Credit bureau notices**, which many states require for larger breaches.
- **Contracts.** Customer and vendor agreements often set shorter deadlines than any law.
- **Other industry rules**, such as banking regulators, state insurance laws and NYDFS.
- **Other countries**, apart from the EU's GDPR.
- **Public holidays.** Business-day deadlines skip weekends only.
- **State-specific letter wording.** The draft letter is a general starting point. Several states require particular content.

---

## What's in the folder

```text
.
├── run.py                        # Start here: python run.py
├── config/
│   └── regulations.json          # All the law data, in one file
├── examples/
│   └── sample_incident.json      # Copy this to describe your incident
├── src/
│   ├── compliance_engine.py      # Decides which laws apply and counts the days
│   ├── drafter.py                # Writes the HTML report and letter
│   └── predict.py                # Experimental (see below)
├── templates/
│   ├── report.html               # Layout of the report
│   └── us_consumer_notice.html   # Layout of the draft letter
├── tests/                        # Automated checks
└── output/                       # Your reports appear here (not saved to git)
```

To run the automated checks:

```bash
pip install -r requirements-dev.txt
pytest
```

### Experimental: fine estimator

`src/predict.py` is a separate toy that guesses a regulatory fine from the number of records and company revenue. It learns from 25 illustrative rows written inside the script, which is far too little to predict anything. Do not use its output for decisions. It needs extra packages: `pip install -r requirements-predict.txt`, then `python src/predict.py`.

---

### Disclaimer

This tool is provided **as-is** for educational and portfolio purposes only. It is **not** legal advice and is **not** a substitute for legal counsel or a professional compliance assessment.

The author makes no guarantees regarding the accuracy, completeness, or regulatory sufficiency of any output produced by this tool. **Use at your own risk.** The author assumes no liability for decisions made based on this tool's output. See the [MIT License](LICENSE) for full terms.

---

### License

[MIT](LICENSE)
