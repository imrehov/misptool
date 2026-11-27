import base64
import binascii
import json
import re
import tempfile
from pathlib import Path
from typing import Any


def normalize_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_event, dict):
        raise RuntimeError("MISP export returned an invalid event")
    event = raw_event.get("Event", raw_event)
    if not isinstance(event, dict) or event.get("id") is None or not str(event.get("id", "")).strip():
        raise RuntimeError("MISP export returned an event without an ID")
    return event


def fetch_all_events(misp, with_attachments: bool = False) -> list[dict[str, Any]]:
    return _fetch_events(misp, with_attachments)


def fetch_recent_events(misp, lookback_minutes: int, with_attachments: bool = False) -> list[dict[str, Any]]:
    if lookback_minutes <= 0:
        raise ValueError("Export lookback_minutes must be positive")
    return _fetch_events(misp, with_attachments, timestamp=f"{lookback_minutes}m")


def _fetch_events(misp, with_attachments: bool, **filters) -> list[dict[str, Any]]:
    # shortcut: collects the export in memory; stream pages when exports exceed available RAM.
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = 1
    while True:
        events = misp.search(
            controller="events", return_format="json", pythonify=False,
            metadata=False, with_attachments=with_attachments, limit=100, page=page,
            **filters,
        )
        if isinstance(events, dict):
            if "errors" in events or "error" in events:
                raise RuntimeError(f"MISP event export failed on page {page}: API error")
            events = events.get("response")
        if not isinstance(events, list):
            raise RuntimeError(f"MISP event export failed on page {page}: unexpected response")
        if not events:
            return result
        before = len(result)
        for raw_event in events:
            event = normalize_event(raw_event)
            event_id = str(event["id"])
            if event_id not in seen:
                result.append(event)
                seen.add(event_id)
        if len(result) == before:
            raise RuntimeError("MISP export pagination returned no new events; export aborted")
        page += 1


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

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as f:
            temporary_path = Path(f.name)
            json.dump(events, f, indent=2, ensure_ascii=False)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _safe_component(value: Any, fallback: str) -> str:
    leaf = Path(str(value).replace("\\", "/")).name
    return re.sub(r"[^\w.-]", "_", leaf).strip(".")[:120] or fallback


def dump_inline_attachments(events: list[dict[str, Any]], attachments_dir: str) -> int:
    base_dir = Path(attachments_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for event_index, event in enumerate(events, start=1):
        event_id = _safe_component(event.get("id", ""), f"event_{event_index}")
        event_dir = base_dir / event_id
        if not event_dir.resolve().is_relative_to(base_dir):
            raise ValueError("Attachment event directory points outside the export directory")
        event_dir.mkdir(parents=True, exist_ok=True)

        attributes = list(event.get("Attribute", []) or [])
        for obj in event.get("Object", []) or []:
            attributes.extend(obj.get("Attribute", []) or [])
        for index, attr in enumerate(attributes, start=1):
            if str(attr.get("type", "")) not in {"attachment", "malware-sample"}:
                continue
            if "data" not in attr:
                continue

            filename = f"{index}_{_safe_component(attr.get('value', ''), 'attachment')}"
            data = attr.get("data")

            try:
                raw = base64.b64decode(data, validate=True)
            except (binascii.Error, ValueError, TypeError) as error:
                raise ValueError(f"Invalid base64 attachment data in event {event_id}") from error

            # Exclusive creation prevents overwriting existing files or following file symlinks.
            with (event_dir / filename).open("xb") as f:
                f.write(raw)
            count += 1
    return count
