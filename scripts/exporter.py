import base64
import json
from pathlib import Path
from typing import Any


def normalize_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    return raw_event.get("Event", raw_event)


def fetch_all_events(misp) -> list[dict[str, Any]]:
    events = misp.events(pythonify=False)
    if isinstance(events, dict) and "response" in events:
        events = events["response"]
    return [normalize_event(e) for e in events]


def fetch_recent_events(misp, lookback_minutes: int) -> list[dict[str, Any]]:
    events = misp.search(
        controller="events",
        timestamp=f"{lookback_minutes}m",
        pythonify=False,
    )
    if isinstance(events, dict) and "response" in events:
        events = events["response"]
    return [normalize_event(e) for e in events]


def extract_attachment_metadata(event: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for attr in event.get("Attribute", []) or []:
        attr_type = str(attr.get("type", ""))
        if attr_type in {"attachment", "malware-sample"}:
            results.append({
                "id": attr.get("id"),
                "uuid": attr.get("uuid"),
                "type": attr_type,
                "category": attr.get("category"),
                "value": attr.get("value"),
                "filename": attr.get("value"),
                "has_data": "data" in attr,
            })

    for obj in event.get("Object", []) or []:
        for attr in obj.get("Attribute", []) or []:
            attr_type = str(attr.get("type", ""))
            if attr_type in {"attachment", "malware-sample"}:
                results.append({
                    "id": attr.get("id"),
                    "uuid": attr.get("uuid"),
                    "object_name": obj.get("name"),
                    "type": attr_type,
                    "category": attr.get("category"),
                    "value": attr.get("value"),
                    "filename": attr.get("value"),
                    "has_data": "data" in attr,
                })

    return results


def save_events_json(events: list[dict[str, Any]], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)


def dump_inline_attachments(events: list[dict[str, Any]], attachments_dir: str) -> None:
    base_dir = Path(attachments_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    for event in events:
        event_id = str(event.get("id", "unknown"))
        event_dir = base_dir / event_id
        event_dir.mkdir(parents=True, exist_ok=True)

        for attr in event.get("Attribute", []) or []:
            if str(attr.get("type", "")) not in {"attachment", "malware-sample"}:
                continue
            if "data" not in attr:
                continue

            filename = str(attr.get("value", f"attr_{attr.get('id', 'unknown')}"))
            data = attr.get("data")

            try:
                raw = base64.b64decode(data)
            except Exception:
                continue

            (event_dir / filename).write_bytes(raw)