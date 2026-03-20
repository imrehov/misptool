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

---

## Notes

- Do not commit API keys or webhooks
- Use LAN URL instead of localhost for team access
- Deleting `state.json` resets history

---

## Summary

Smart triage layer for MISP to reduce noise and highlight meaningful changes.
