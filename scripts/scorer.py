import hashlib
import json
from typing import Any


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    if "Event" in event and isinstance(event["Event"], dict):
        return event["Event"]
    return event


def count_attributes(event: dict[str, Any]) -> int:
    attributes = event.get("Attribute", [])
    return len(attributes) if isinstance(attributes, list) else 0


def count_objects(event: dict[str, Any]) -> int:
    objects = event.get("Object", [])
    return len(objects) if isinstance(objects, list) else 0


def get_tags(event: dict[str, Any]) -> list[dict[str, Any]]:
    tags = event.get("Tag", [])
    return tags if isinstance(tags, list) else []


def get_tag_names(event: dict[str, Any]) -> list[str]:
    names: list[str] = []

    for tag in get_tags(event):
        name = str(tag.get("name", "")).strip()
        if name:
            names.append(name)

    return sorted(names)


def get_galaxy_tag_names(event: dict[str, Any]) -> list[str]:
    return sorted(
        [tag_name for tag_name in get_tag_names(event) if tag_name.startswith("misp-galaxy:")]
    )


def count_galaxy_tags(event: dict[str, Any]) -> int:
    return len(get_galaxy_tag_names(event))


def score_event(event: dict[str, Any], config: dict[str, Any]) -> int:
    event = normalize_event(event)
    scoring_cfg = config.get("scoring", {})

    score = 0

    info = str(event.get("info", "")).lower()
    threat_level_id = str(event.get("threat_level_id", ""))
    attribute_count = count_attributes(event)
    object_count = count_objects(event)
    tag_count = len(get_tag_names(event))
    galaxy_tag_count = count_galaxy_tags(event)
    published = bool(event.get("published", False))

    keywords = scoring_cfg.get("keywords", {})
    for keyword, keyword_score in keywords.items():
        if keyword.lower() in info:
            score += int(keyword_score)

    threat_scores = scoring_cfg.get("threat_level_scores", {})
    score += int(threat_scores.get(threat_level_id, 0))

    for threshold in scoring_cfg.get("attribute_thresholds", []):
        count = int(threshold.get("count", 0))
        threshold_score = int(threshold.get("score", 0))
        if attribute_count >= count:
            score += threshold_score

    if published:
        score += int(scoring_cfg.get("published_score", 0))

    if tag_count > 0:
        score += int(scoring_cfg.get("tag_count_score", 0))

    if galaxy_tag_count > 0:
        score += int(scoring_cfg.get("galaxy_tag_score", 0))

    if object_count > 0:
        score += int(scoring_cfg.get("object_score", 0))

    noisy_keywords = scoring_cfg.get("noisy_title_keywords", [])
    noisy_penalty = int(scoring_cfg.get("noisy_penalty", 0))
    for keyword in noisy_keywords:
        if keyword.lower() in info:
            score -= noisy_penalty
            break

    return score


def is_interesting(event: dict[str, Any], config: dict[str, Any]) -> bool:
    scoring_cfg = config.get("scoring", {})
    min_score = int(scoring_cfg.get("min_score", 3))
    return score_event(event, config) >= min_score


def build_event_snapshot(event: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    event = normalize_event(event)

    snapshot = {
        "event_id": str(event.get("id", "")),
        "info": str(event.get("info", "")).strip(),
        "date": str(event.get("date", "")),
        "timestamp": str(event.get("timestamp", "")),
        "publish_timestamp": str(event.get("publish_timestamp", "")),
        "published": bool(event.get("published", False)),
        "threat_level_id": str(event.get("threat_level_id", "")),
        "analysis": str(event.get("analysis", "")),
        "tag_names": get_tag_names(event),
        "galaxy_tag_names": get_galaxy_tag_names(event),
        "attribute_count": count_attributes(event),
        "object_count": count_objects(event),
        "score": score_event(event, config),
    }

    snapshot["fingerprint"] = make_event_fingerprint(snapshot)
    return snapshot


def make_event_fingerprint(snapshot: dict[str, Any]) -> str:
    hash_input = dict(snapshot)
    hash_input.pop("fingerprint", None)

    serialized = json.dumps(
        hash_input,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def summarize_event(event: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    snapshot = build_event_snapshot(event, config)

    return {
        "change_reason": "",
        "id": snapshot["event_id"],
        "info": snapshot["info"],
        "date": snapshot["date"],
        "timestamp": snapshot["timestamp"],
        "publish_timestamp": snapshot["publish_timestamp"],
        "published": snapshot["published"],
        "threat_level_id": snapshot["threat_level_id"],
        "analysis": snapshot["analysis"],
        "attribute_count": snapshot["attribute_count"],
        "object_count": snapshot["object_count"],
        "tag_count": len(snapshot["tag_names"]),
        "galaxy_tag_count": len(snapshot["galaxy_tag_names"]),
        "tag_names": snapshot["tag_names"],
        "galaxy_tag_names": snapshot["galaxy_tag_names"],
        "score": snapshot["score"],
        "fingerprint": snapshot["fingerprint"],
        "change_summary": [],
    }