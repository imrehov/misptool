# MISPTool

A lightweight CLI tool for **monitoring, filtering, and alerting on meaningful MISP event changes**.

Designed for blue team / CTF / SOC environments where large volumes of automated data are pushed into MISP, but only **enriched or relevant events** should trigger attention.

---

## Key Features

- Polls MISP for recent events
- Tracks event state locally (`state.json`)
- Detects **changes using hashing (fingerprints)**
- Classifies events as:
  - 🆕 **NEW EVENT** (first time seen)
  - 🔄 **UPDATED** (changed)
  - 🧠 **ENRICHED** (gained useful data)
- Scores events using configurable rules
- Sends alerts to:
  - Terminal
  - Discord webhook
- Imports:
  - single galaxy cluster JSON
  - entire folders of cluster JSONs

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Commands

```bash
python main.py <command>
```

### Available commands

- test-connection
- test-storage
- test-scorer
- run-once
- run
- import-cluster
- import-all
- list-galaxies
- create-galaxy

---

## Example Usage

```bash
python main.py run
```


## Importing clusters

When importing a single `.json` file, run `python main.py import-cluster filename.json`.
when importing `.json` files from a folder, run `python main.py import-all folder/`.

## Accepted cluster format

Mandatory fields:
- value
- type
- description

```json
{
    "value": "cluster_name",
    "type": "galaxy_type",
    "source": "source",
    "authors": "authors",
    "description": "cluster_description",
    "distribution": 3, _1 is org only, 2 for connected, 3 all communities
    "GalaxyElement": [
        {
            "key": "Any useful information",
            "value": "about the cluster"
        },
        {
            "key": "Example: Primary Target",
            "value": "Example: Antarctica"
        }
    ]
}
```
---

## Summary

Smart triage layer for MISP to reduce noise and highlight meaningful changes.
