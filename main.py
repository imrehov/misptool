import argparse

from src.misptool.config import Config
from src.misptool.application.cli_commands import CliCommands

from datetime import date

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

    migrate_state_parser = subparsers.add_parser(
        "migrate-state",
        help="Migrate local JSON state into PostgreSQL",
    )
    migrate_state_parser.add_argument(
        "--input",
        default="state.json",
        help="Path to JSON state file",
    )
    
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

    export_parser = subparsers.add_parser(
    "export-events",
    help="Export events to JSON for offline study",
    )
    export_parser.add_argument(
        "--output",
        default=f"exports-{date.today()}/events.json",
        help="Output JSON file path",
    )
    export_parser.add_argument(
        "--recent",
        action="store_true",
        help="Export only recent events using lookback_minutes from config",
    )
    export_parser.add_argument(
        "--with-attachments",
        action="store_true",
        help="Also dump attachment/sample content when available",
    )

    args = parser.parse_args()

    if args.command == "test-connection":
        CliCommands(args.config).test_connection()

    elif args.command == "test-storage":
        CliCommands(args.config).test_storage()

    elif args.command == "test-scorer":
        CliCommands(args.config).test_scorer()

    elif args.command == "run-once":
        CliCommands(args.config).run_once()
        

    elif args.command == "run":
        CliCommands(args.config).run_loop()

    elif args.command == "migrate-state":
        CliCommands(args.config).migrate_state(args.input)

    elif args.command == "import-cluster":
        CliCommands(args.config).import_cluster(args.json_path)

    elif args.command == "import-all":
        CliCommands(args.config).import_all(args.folder_path)

    elif args.command == "list-galaxies":
        CliCommands(args.config).list_galaxies()

    elif args.command == "create-galaxy":
        CliCommands(args.config).create_galaxy(
            name=args.name,
            galaxy_type=args.type,
            description=args.description,
            namespace=args.namespace,
            icon=args.icon,
        )

    elif args.command == "ensure-galaxies":
        CliCommands(args.config).ensure_galaxies()

    elif args.command == "export-events":
        CliCommands(args.config).export_events(args.output, args.recent, args.with_attachments)

if __name__ == "__main__":
    main()
