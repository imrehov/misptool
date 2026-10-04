from scripts.misp_client import build_misp_client
from src.misptool.config import Config
from src.misptool.infrastructure.notifications.notifier import Notifier
from src.misptool.domain.scorer import Scorer
from src.misptool.infrastructure.filesystem.storage import Storage
from src.misptool.application.event_processor import EventProcessor


class CliHandler:
    def __init__(self, config_path: str):
        self.config = Config(config_path)

    def run_once(self) -> None:
        misp = build_misp_client(self.config)
        repo = Storage()
        scorer = Scorer(self.config)
        notifier = Notifier(self.config)
        
        processor = EventProcessor(
            misp_client=misp,
            repo=repo,
            scorer=scorer,
            notifier=notifier,
            config=self.config,
            )
        
        processor.process_events()

    def cmd_test_scorer(self) -> None:
        misp = build_misp_client(self.config)
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


    