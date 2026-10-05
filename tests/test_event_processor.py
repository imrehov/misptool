from src.misptool.application.event_processor import EventProcessor
from src.misptool.domain.scorer import Scorer
from src.misptool.infrastructure.filesystem.storage import Storage


class FakeMispClient:
    def __init__(self, events):
        self.events = events

    def search(self, **kwargs):
        return self.events


class FakeNotifier:
    def __init__(self):
        self.console_messages = []
        self.discord_messages = []

    def notify_console(self, summary):
        self.console_messages.append(summary)

    def notify_discord(self, summary):
        self.discord_messages.append(summary)


def test_new_interesting_event_is_stored_and_alerted(tmp_path):
    config = {
        "polling": {"lookback_minutes": 10},
        "misp": {"url": "https://misp.example"},
        "notifications": {"discord_userid": "123"},
        "scoring": {
            "min_score": 1,
            "keywords": {"apt": 5},
        },
    }

    event = {
        "Event": {
            "id": "42",
            "info": "APT activity",
            "date": "2026-10-05",
            "timestamp": "1000",
            "publish_timestamp": "1001",
            "published": True,
            "threat_level_id": "1",
            "analysis": "0",
            "Attribute": [],
            "Object": [],
            "Tag": [],
        }
    }

    misp = FakeMispClient([event])
    storage = Storage(str(tmp_path / "state.json"))
    scorer = Scorer(config)
    notifier = FakeNotifier()

    processor = EventProcessor(
        misp_client=misp,
        repo=storage,
        scorer=scorer,
        notifier=notifier,
        config=config,
    )

    processor.process_events()

    saved_state = storage.get_event_state("42")

    assert saved_state is not None
    assert saved_state["event_id"] == "42"
    assert saved_state["score"] >= 1
    assert len(notifier.console_messages) == 1
    assert notifier.console_messages[0]["change_reason"] == "new"

def test_unchanged_event_does_not_alert_twice(tmp_path):
    config = {
        "polling": {"lookback_minutes": 10},
        "misp": {"url": "https://misp.example"},
        "notifications": {"discord_userid": "123"},
        "scoring": {
            "min_score": 1,
            "keywords": {"apt": 5},
        },
    }

    event = {
        "Event": {
            "id": "42",
            "info": "APT activity",
            "date": "2026-10-05",
            "timestamp": "1000",
            "publish_timestamp": "1001",
            "published": True,
            "threat_level_id": "1",
            "analysis": "0",
            "Attribute": [],
            "Object": [],
            "Tag": [],
        }
    }

    storage = Storage(str(tmp_path / "state.json"))

    first_notifier = FakeNotifier()
    first_processor = EventProcessor(
        misp_client=FakeMispClient([event]),
        repo=storage,
        scorer=Scorer(config),
        notifier=first_notifier,
        config=config,
    )
    first_result = first_processor.process_events()

    second_notifier = FakeNotifier()
    second_processor = EventProcessor(
        misp_client=FakeMispClient([event]),
        repo=storage,
        scorer=Scorer(config),
        notifier=second_notifier,
        config=config,
    )
    second_result = second_processor.process_events()

    assert first_result["alerted"] == 1
    assert second_result["changed"] == 0
    assert second_result["alerted"] == 0
    assert len(second_notifier.console_messages) == 0