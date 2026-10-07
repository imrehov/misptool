
from src.misptool.infrastructure.notifications.notifier import Notifier
from src.misptool.domain.scorer import Scorer
from src.misptool.infrastructure.filesystem.storage import Storage
from src.misptool.application.event_processor import EventProcessor
from src.misptool.config import Config
from src.misptool.application.ports import EventStateRepository

from scripts.galaxy_importer import import_cluster_from_file, import_clusters_from_folder
from scripts.galaxy_admin import list_galaxies, create_galaxy, ensure_galaxy

from datetime import datetime
from rich.pretty import pprint
from contextlib import contextmanager
from typing import Iterator



class CliCommands:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
    
    @property
    def config(self):
        if self._config is None:
            self._config = Config(self.config_path)
        return self._config

    @contextmanager
    def event_state_repository(self) -> Iterator[EventStateRepository]:
        storage_cfg = self.config.get("storage", {})
        backend = storage_cfg.get("backend", "json")

        if backend == "postgres":
            from src.misptool.infrastructure.db.session import DbSession
            from src.misptool.infrastructure.db.repositories import PostgresEventStateRepository

            database_url_env = storage_cfg.get("database_url_env", "MISP_DB_URL")
            db = DbSession(database_url_env=database_url_env)

            with db.session() as session:
                yield PostgresEventStateRepository(session)
            return

        if backend == "json":
            yield Storage()
            return

        raise ValueError(f"Unsupported storage backend: {backend}")

    def now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def build_misp(self):
        from src.misptool.infrastructure.misp_client import MispClient

        return MispClient(self.config)

    def build_processor(self, repo: EventStateRepository):
        return EventProcessor(
            misp_client=self.build_misp(),
            repo=repo,
            scorer=Scorer(self.config),
            notifier=Notifier(self.config),
            config=self.config,
        )

    def run_once(self) -> None:

        with self.event_state_repository() as repo:
            self.build_processor(repo).process_events()

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

    def import_cluster(self, json_path) -> None:
        misp = self.build_misp()

        pprint(import_cluster_from_file(misp, json_path))

    def import_all(self, folder_path) -> None:
        misp = self.build_misp()

        result = import_clusters_from_folder(misp, folder_path)

        print(f"Folder: {result['folder']}")
        print(f"Total JSON files: {result['total']}")
        print(f"Successful imports: {result['success_count']}")
        print(f"Failed imports: {result['failure_count']}")

        for item in result["results"]:
            if item["status"] == "success":
                print(f"[OK] {item['file']}")
            else:
                print(f"[ERR] {item['file']}: {item['error']}")
    
    def create_galaxy(self, name, galaxy_type, description, namespace, icon) -> None:
        misp = self.build_misp()

        result = create_galaxy(
            misp=misp,
            name=name,
            galaxy_type=galaxy_type,
            description=description,
            namespace=namespace,
            icon=icon,
        )

        pprint(result)

    def ensure_galaxies(self) -> None:
        misp = self.build_misp()

        ta_result = ensure_galaxy(
            misp=misp,
            name="Threat Actor",
            galaxy_type="threat-actor",
            description="Threat actors are malicious actors or adversaries.",
            namespace="custom",
            icon="user-secret",
        )
        pprint(ta_result)

        campaign_result = ensure_galaxy(
            misp=misp,
            name="Campaign",
            galaxy_type="campaign",
            description="Campaigns represent specific adversary operations.",
            namespace="custom",
            icon="bullseye",
        )
        pprint(campaign_result)

    def export_events(self, output, recent=False, with_attachments=False) -> None:
        misp = self.build_misp()

        from scripts.exporter import (
            fetch_all_events,
            fetch_recent_events,
            save_events_json,
            dump_inline_attachments,
        )

        if recent:
            lookback_minutes = self.config.get("polling", {}).get("lookback_minutes", 10)
            events = fetch_recent_events(misp, lookback_minutes)
        else:
            events = fetch_all_events(misp)

        save_events_json(events, output)
        print(f"Exported {len(events)} event(s) to {output}")

        if with_attachments:
            dump_inline_attachments(events, f"exports-{datetime.today()}/attachments")
            print("Attachment dump completed.")

    def run_loop(self) -> None:
        interval_seconds = self.config.get("polling", {}).get("interval_seconds", 60)      
        lookback_minutes = self.config.get("polling", {}).get("lookback_minutes", 10)
        import time
        
        print(f"[{self.now_str()}] - Starting loop. Polling every {interval_seconds} seconds.")
        print(f"[{self.now_str()}] - Fetching events from the last {lookback_minutes} minute(s).")

        while True:
            try:
                with self.event_state_repository() as repo:
                    self.build_processor(repo).process_events()
            
            except Exception as e:
                print("Error during run: ", e)
            
            time.sleep(interval_seconds)


    
