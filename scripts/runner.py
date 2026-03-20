import time
from typing import Any
from datetime import datetime

from scripts.storage import Storage
from scripts.scorer import build_event_snapshot, is_interesting, summarize_event
from scripts.notifier import notify_console, notify_discord

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_events(misp, lookback_minutes: int) -> list[dict[str, Any]]:
    return misp.search(
        controller="events",
        timestamp=f"{lookback_minutes}m",
        pythonify=False,
    )


def has_event_changed(old_state: dict[str, Any] | None, new_state: dict[str, Any]) -> bool:
    if old_state is None:
        return True

    return old_state.get("fingerprint") != new_state.get("fingerprint")


def event_became_more_interesting(
    old_state: dict[str, Any] | None,
    new_state: dict[str, Any],
) -> bool:
    if old_state is None:
        return False

    if int(new_state.get("score", 0)) > int(old_state.get("score", 0)):
        return True

    if int(new_state.get("attribute_count", 0)) > int(old_state.get("attribute_count", 0)):
        return True

    if int(new_state.get("object_count", 0)) > int(old_state.get("object_count", 0)):
        return True

    if len(new_state.get("galaxy_tag_names", [])) > len(old_state.get("galaxy_tag_names", [])):
        return True

    if len(new_state.get("tag_names", [])) > len(old_state.get("tag_names", [])):
        return True

    old_published = bool(old_state.get("published", False))
    new_published = bool(new_state.get("published", False))
    if not old_published and new_published:
        return True

    return False

def build_change_summary(
    old_state: dict[str, Any] | None,
    new_state: dict[str, Any],
) -> list[str]:
    if old_state is None:
        return ["new event"]

    changes: list[str] = []

    old_score = int(old_state.get("score", 0))
    new_score = int(new_state.get("score", 0))
    if old_score != new_score:
        changes.append(f"score: {old_score} -> {new_score}")

    old_attr = int(old_state.get("attribute_count", 0))
    new_attr = int(new_state.get("attribute_count", 0))
    if old_attr != new_attr:
        changes.append(f"attributes: {old_attr} -> {new_attr}")

    old_obj = int(old_state.get("object_count", 0))
    new_obj = int(new_state.get("object_count", 0))
    if old_obj != new_obj:
        changes.append(f"objects: {old_obj} -> {new_obj}")

    old_published = bool(old_state.get("published", False))
    new_published = bool(new_state.get("published", False))
    if old_published != new_published:
        changes.append(f"published: {old_published} -> {new_published}")

    old_tags = set(old_state.get("tag_names", []))
    new_tags = set(new_state.get("tag_names", []))

    added_tags = sorted(new_tags - old_tags)
    removed_tags = sorted(old_tags - new_tags)

    if added_tags:
        changes.append("tags added: " + ", ".join(added_tags[:3]))
    if removed_tags:
        changes.append("tags removed: " + ", ".join(removed_tags[:3]))

    old_galaxy = set(old_state.get("galaxy_tag_names", []))
    new_galaxy = set(new_state.get("galaxy_tag_names", []))

    added_galaxy = sorted(new_galaxy - old_galaxy)
    removed_galaxy = sorted(old_galaxy - new_galaxy)

    if added_galaxy:
        changes.append("galaxy added: " + ", ".join(added_galaxy[:3]))
    if removed_galaxy:
        changes.append("galaxy removed: " + ", ".join(removed_galaxy[:3]))

    return changes

def process_events(
    misp,
    storage,
    config,
    lookback_minutes,
    discord_webhook=None,
) -> None:

    misp_url = config.get("misp", {}).get("url", "")
    events = fetch_events(misp, lookback_minutes)

    if not events:
        print(f"[{now_str()}] - No events fetched.")
        return

    print(f"[{now_str()}] - Fetched {len(events)} event(s).")

    changed_count = 0
    alerted_count = 0

    for raw_event in events:
        event = raw_event.get("Event", raw_event)
        event_id = str(event.get("id", "")).strip()

        print(f"[DEBUG] storage path: {storage.path.resolve()}")
        print(f"[DEBUG] event_id={event_id!r}")
        print(f"[DEBUG] known ids sample={list(storage.events.keys())[:10]}")
        print(f"[DEBUG] old_state={storage.get_event_state(event_id)}")

        if not event_id:
            continue

        old_state = storage.get_event_state(event_id)
        new_state = build_event_snapshot(event, config)
        change_summary = build_change_summary(old_state, new_state)

        changed = has_event_changed(old_state, new_state)
        interesting = is_interesting(event, config)
        more_interesting = event_became_more_interesting(old_state, new_state)

        print(f"[DEBUG] changed={changed}")
        print(f"[DEBUG] interesting={interesting}")
        print(f"[DEBUG] more_interesting={more_interesting}")

        if not changed:
            continue

        changed_count += 1

        should_alert = False
        reason = "updated"

        print(f"[DEBUG] storage path: {storage.path.resolve()}")
        print(f"[DEBUG] event_id={event_id!r}")
        print(f"[DEBUG] known ids sample={list(storage.events.keys())[:10]}")
        print(f"[DEBUG] old_state={storage.get_event_state(event_id)}")

        if old_state is None:
            reason = "new"
            if interesting:
                should_alert = True
        else:
            if interesting:
                should_alert = True
                if more_interesting:
                    reason = "enriched"
                else:
                    reason = "updated"

        print(f"[DEBUG] should_alert={should_alert}, reason={reason}")

        if should_alert:
            summary = summarize_event(event, config)
            summary["change_reason"] = reason
            summary["change_summary"] = change_summary

            notify_console(summary)

            if discord_webhook:
                misp_url = config.get("misp", {}).get("url", "")
                notify_discord(summary, discord_webhook, misp_url)

            alerted_count += 1

        storage.update_event_state(event_id, new_state)

    storage.save()

    print(f"[{now_str()}] - Changed events processed: {changed_count}")
    print(f"[{now_str()}] - Interesting events alerted: {alerted_count}")


def run_once(
    misp,
    storage: Storage,
    config: dict[str, Any],
    lookback_minutes: int,
    discord_webhook: str | None = None,
) -> None:
    process_events(
        misp=misp,
        storage=storage,
        config=config,
        lookback_minutes=lookback_minutes,
        discord_webhook=discord_webhook,
    )


def run_loop(
    misp,
    storage: Storage,
    config: dict[str, Any],
    interval_seconds: int = 300,
    lookback_minutes: int = 10,
    discord_webhook: str | None = None,
) -> None:
    print(f"[{now_str()}] - Starting loop. Polling every {interval_seconds} seconds.")
    print(f"[{now_str()}] - Fetching events from the last {lookback_minutes} minute(s).")

    while True:
        try:
            process_events(
                misp=misp,
                storage=storage,
                config=config,
                lookback_minutes=lookback_minutes,
                discord_webhook=discord_webhook,
            )
        except Exception as e:
            print("Error during run:", e)

        time.sleep(interval_seconds)