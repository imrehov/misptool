from scripts.misp_client import build_misp_client
from src.misptool.config import Config
from src.misptool.infrastructure.notifications.notifier import Notifier
from src.misptool.domain.scorer import Scorer
from src.misptool.infrastructure.filesystem.storage import Storage
from src.misptool.application.event_processor import EventProcessor


class CliCommands:
    def __init__(self, config_path: str):
        self.config = Config(config_path)

    def build_misp(self):
        return build_misp_client(self.config)

    def build_processor(self):
        return EventProcessor(
            misp_client=misp,
            repo=repo,
            scorer=scorer,
            notifier=notifier,
            config=self.config,
        )

    def run_once(self) -> None:
        misp = build_misp()
        repo = Storage()
        scorer = Scorer(self.config)
        notifier = Notifier(self.config)
        
        processor = build_processor()
        
        processor.process_events()

    def test_scorer(self) -> None:
        misp = build_misp()
        scorer = Scorer(self.config)
        notifier = Notifier(self.config)

        events = misp.search(controller="events", limit=5, pythonify=False)

        if not events:
            print("No events returned.")
            return

        for raw_event in events:
            summary = scorer.summarize_event(raw_event, config)
            interesting = scorer.is_interesting(raw_event, config)

            pprint(summary)
            print("interesting:", interesting)

            if interesting:
                notifier.notify_console(summary)

            print("-" * 40)

    def test_storage(self) -> None:
        repo = Storage()
        
        print("Already seen 123?", repo.has_seen_event("123"))

        repo.mark_event_seen("123")
        repo.save()

        print("Already seen 123?", repo.has_seen_event("123"))

    def test_connection(self) -> None:
        misp = build_misp()

        events = misp.search(controller="events", limit=1, pythonify=False)
        print("Connection successful.")

        if not events:
            print("No events returned.")
            return
        
        event = events[0].get("Event", events[0])

        summary = {
            "id": event.get("id"),
            "info": event.get("info"),
            "date": event.get("date"),
            "threat_level_id": event.get("threat_level_id"),
            "analysis": event.get("analysis"),
        }
        print("Sample response:")
        pprint(summary)   
