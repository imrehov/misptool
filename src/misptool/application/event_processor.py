from datetime import datetime
from typing import Any

from src.misptool.config import Config
from src.misptool.domain.scorer import Scorer
from src.misptool.infrastructure import notifications
from src.misptool.infrastructure.filesystem import storage


class EventProcessor:
    def __init__(self, misp_client, repo: storage.Storage, scorer: Scorer, notifier: notifications.notifier.Notifier, config: Config):
        self.misp_client = misp_client
        self.repo = repo
        self.scorer = scorer
        self.notifier = notifier
        self.config = config
    
    def now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def fetch_events(self) -> list[dict[str, Any]]:
        
        lookback_minutes = self.config.get("polling", {}).get("lookback_minutes", {})
        
        return self.misp_client.search(
            controller="events",
            timestamp=f"{lookback_minutes}m",
            pythonify=False,
        )

    def has_event_changed(self, old_state: dict[str, Any] | None, new_state: dict[str, Any]) -> bool:
        if old_state is None:
            return True

        return old_state.get("fingerprint") != new_state.get("fingerprint")

    def event_became_more_interesting(
        self,
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
        self,
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
        self,
    ) -> dict[str, int]:

        misp_url = self.config.get("misp", {}).get("url", "")
        discord_user_to_ping = self.config.get("notifications", {}).get("discord_userid", "")
        events = self.fetch_events()

        if not events:
            print(f"[{self.now_str()}] - No events fetched.")
            return {
                "fetched": 0,
                "changed": 0,
                "alerted": 0,
            }

        print(f"[{self.now_str()}] - Fetched {len(events)} event(s).")

        changed_count = 0
        alerted_count = 0

        for raw_event in events:
            event = raw_event.get("Event", raw_event)
            event_id = str(event.get("id", "")).strip()

            print(f"[DEBUG] storage path: {self.repo.path.resolve()}")
            print(f"[DEBUG] event_id={event_id!r}")
            print(f"[DEBUG] known ids sample={list(self.repo.events.keys())[:10]}")
            print(f"[DEBUG] old_state={self.repo.get_event_state(event_id)}")

            if not event_id:
                continue

            old_state = self.repo.get_event_state(event_id)
            new_state = self.scorer.build_event_snapshot(event)
            change_summary = self.build_change_summary(old_state, new_state)

            changed = self.has_event_changed(old_state, new_state)
            interesting = self.scorer.is_interesting(event)
            more_interesting = self.event_became_more_interesting(old_state, new_state)

            print(f"[DEBUG] changed={changed}")
            print(f"[DEBUG] interesting={interesting}")
            print(f"[DEBUG] more_interesting={more_interesting}")

            if not changed:
                continue

            changed_count += 1

            should_alert = False
            reason = "updated"

            print(f"[DEBUG] storage path: {self.repo.path.resolve()}")
            print(f"[DEBUG] event_id={event_id!r}")
            print(f"[DEBUG] known ids sample={list(self.repo.events.keys())[:10]}")
            print(f"[DEBUG] old_state={self.repo.get_event_state(event_id)}")

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
                summary = self.scorer.summarize_event(event)
                summary["change_reason"] = reason
                summary["change_summary"] = change_summary

                self.notifier.notify_console(summary)

                if discord_user_to_ping:
                    self.notifier.notify_discord(summary)

                alerted_count += 1

            self.repo.update_event_state(event_id, new_state)

        self.repo.save()

        print(f"[{self.now_str()}] - Changed events processed: {changed_count}")
        print(f"[{self.now_str()}] - Interesting events alerted: {alerted_count}")

        return {
            "fetched": len(events),
            "changed": changed_count,
            "alerted": alerted_count,
        }