import argparse
from rich.pretty import pprint

from scripts.config import load_config
from scripts.misp_client import build_misp_client
from scripts.storage import Storage
from scripts.scorer import is_interesting, score_event, summarize_event
from scripts.notifier import notify_console
from scripts.runner import run_loop, run_once

from scripts.galaxy_importer import import_cluster_from_file, import_clusters_from_folder
from scripts.galaxy_admin import list_galaxies, create_galaxy, ensure_galaxy


def cmd_test_connection(config_path: str) -> None:
    config = load_config(config_path)
    misp = build_misp_client(config)

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

def cmd_test_storage() -> None:
    storage = Storage()

    print("Already seen 123?", storage.has_seen_event("123"))

    storage.mark_event_seen("123")
    storage.save()

    print("Marked 123 as seen.")
    print("Already seen 123?", storage.has_seen_event("123"))

def cmd_test_scorer(config_path: str) -> None:
    config = load_config(config_path)
    misp = build_misp_client(config)

    events = misp.search(controller="events", limit=5, pythonify=False)

    if not events:
        print("No events returned.")
        return

    for raw_event in events:
        summary = summarize_event(raw_event, config)
        interesting = is_interesting(raw_event, config)

        pprint(summary)
        print("interesting:", interesting)

        if interesting:
            notify_console(summary)

        print("-" * 40)


def main() -> None:
    parser = argparse.ArgumentParser(description="Blue Team MISP helper")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML config file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("test-connection", help="Test MISP API connection")
    subparsers.add_parser("test-storage", help="Test local storage")
    subparsers.add_parser("test-scorer", help="Test event scoring")
    subparsers.add_parser("run-once", help="Run one processing cycle")
    subparsers.add_parser("run", help="Run continuously")
    
    import_cluster_parser = subparsers.add_parser(
        "import-cluster",
        help="Import a galaxy cluster from a JSON file",
    )
    import_cluster_parser.add_argument(
        "json_path",
        help="Path to the cluster JSON file",
    )

    import_all_parser = subparsers.add_parser(
        "import-all",
        help="Import all galaxy clusters from a folder of JSON files",
    )
    import_all_parser.add_argument(
        "folder_path",
        help="Path to folder containing cluster JSON files",
    )

    subparsers.add_parser("list-galaxies", help="List available galaxies")

    create_galaxy_parser = subparsers.add_parser(
        "create-galaxy",
        help="Create a galaxy",
    )
    create_galaxy_parser.add_argument("--name", required=True, help="Galaxy name")
    create_galaxy_parser.add_argument("--type", required=True, help="Galaxy type")
    create_galaxy_parser.add_argument(
        "--description",
        required=True,
        help="Galaxy description",
    )
    create_galaxy_parser.add_argument(
        "--namespace",
        default="custom",
        help="Galaxy namespace",
    )
    create_galaxy_parser.add_argument(
        "--icon",
        default="user-secret",
        help="Galaxy icon",
    )

    ensure_galaxies_parser = subparsers.add_parser(
        "ensure-galaxies",
        help="Ensure required galaxies exist",
    )

    args = parser.parse_args()

    if args.command == "test-connection":
        cmd_test_connection(args.config)
        
    elif args.command == "test-storage":
        cmd_test_storage()

    elif args.command == "test-scorer":
        cmd_test_scorer(args.config)

    elif args.command == "run-once":
        config = load_config(args.config)
        misp = build_misp_client(config)
        storage = Storage()
        notifications_cfg = config.get("notifications", {})
        webhook = notifications_cfg.get("discord_webhook")

        polling_cfg = config.get("polling", {})
        lookback_minutes = polling_cfg.get("lookback_minutes", 10)

        run_once(
            misp,
            storage,
            config=config,
            lookback_minutes=lookback_minutes,
            discord_webhook=webhook,
        )

    elif args.command == "run":
        config = load_config(args.config)
        misp = build_misp_client(config)
        storage = Storage()
        notifications_cfg = config.get("notifications", {})
        webhook = notifications_cfg.get("discord_webhook")

        polling_cfg = config.get("polling", {})
        interval_seconds = polling_cfg.get("interval_seconds", 60)
        lookback_minutes = polling_cfg.get("lookback_minutes", 10)

        run_loop(
            misp,
            storage,
            config=config,
            interval_seconds=interval_seconds,
            lookback_minutes=lookback_minutes,
            discord_webhook=webhook,
        )

    elif args.command == "import-cluster":
        config = load_config(args.config)
        misp = build_misp_client(config)

        result = import_cluster_from_file(misp, args.json_path)
        pprint(result)

    elif args.command == "import-all":
        config = load_config(args.config)
        misp = build_misp_client(config)

        result = import_clusters_from_folder(misp, args.folder_path)

        print(f"Folder: {result['folder']}")
        print(f"Total JSON files: {result['total']}")
        print(f"Successful imports: {result['success_count']}")
        print(f"Failed imports: {result['failure_count']}")

        for item in result["results"]:
            if item["status"] == "success":
                print(f"[OK] {item['file']}")
            else:
                print(f"[ERR] {item['file']}: {item['error']}")
    
    elif args.command == "list-galaxies":
        config = load_config(args.config)
        misp = build_misp_client(config)
        pprint(list_galaxies(misp))

    elif args.command == "create-galaxy":
        config = load_config(args.config)
        misp = build_misp_client(config)

        result = create_galaxy(
            misp=misp,
            name=args.name,
            galaxy_type=args.type,
            description=args.description,
            namespace=args.namespace,
            icon=args.icon,
        )
        pprint(result)

    elif args.command == "ensure-galaxies":
        config = load_config(args.config)
        misp = build_misp_client(config)

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

if __name__ == "__main__":
    main()