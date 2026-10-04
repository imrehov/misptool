from src.misptool.config import Config
from src.misptool.infrastructure.notifications.notifier import Notifier
from src.misptool.domain.scorer import Scorer
from src.misptool.infrastructure.filesystem.storage import Storage
from src.misptool.application.event_processor import EventProcessor

from scripts.galaxy_admin import list_galaxies

from rich.pretty import pprint

class CliCommands:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
    
    @property
    def config(self):
        if self._config is None:
            self._config = Config(self.config_path)
        return self._config

    def build_misp(self):

        from scripts.misp_client import build_misp_client

        return build_misp_client(self.config)

    def build_processor(self):
        return EventProcessor(
            misp_client=self.build_misp(),
            repo=Storage(),
            scorer=Scorer(self.config),
            notifier=Notifier(self.config),
            config=self.config,
        )

    def run_once(self) -> None:

        self.build_processor().process_events()

    def test_scorer(self) -> None:
        misp = self.build_misp()
        scorer = Scorer(self.config)
        notifier = Notifier(self.config)

        events = misp.search(controller="events", limit=5, pythonify=False)

        if not events:
            print("No events returned.")
            return

        for raw_event in events:
            summary = scorer.summarize_event(raw_event)
            interesting = scorer.is_interesting(raw_event)

            pprint(summary)
            print("interesting:", interesting)

            if interesting:
                notifier.notify_console(summary)

            print("-" * 40)

    def test_storage(self) -> None:
        repo = Storage()
        
        print("Already seen 123?", repo.get_event_state("123"))

        repo.update_event_state("123", {"event_id": "123"})
        repo.save()

        print("Already seen 123?", repo.get_event_state("123"))

    def test_connection(self) -> None:
        misp = self.build_misp()

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

    def list_galaxies(self) -> None:
        misp = self.build_misp()
        pprint(list_galaxies(misp))
