import json
from pathlib import Path
from typing import Any


ALLOWED_CLUSTER_TYPES = {
    #lspr26 specifikus
    "ls26-threat-actors",
    "180e72d7-b803-469a-99d9-055ddd415884",

    #általános
    "threat-actor"
}

REQUIRED_FIELDS = {
    "value",
    "type",
    "description",
}

def get_galaxy_by_type(misp, galaxy_type: str):
    galaxies = misp.galaxies(pythonify=False)

    # PyMISP/MISP responses can vary a bit, so normalize
    if isinstance(galaxies, dict) and "response" in galaxies:
        galaxies = galaxies["response"]

    for item in galaxies:
        galaxy = item.get("Galaxy", item)
        if str(galaxy.get("type", "")).strip() == galaxy_type:
            return galaxy

    raise ValueError(f"No galaxy found in MISP with type: {galaxy_type}")

def load_cluster_json(path: str) -> dict[str, Any]:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Cluster JSON must contain a top-level object.")

    return data


def validate_cluster_data(data: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    cluster_type = str(data["type"]).strip()
    if cluster_type not in ALLOWED_CLUSTER_TYPES:
        raise ValueError(
            f"Unsupported cluster type: {cluster_type}. "
            f"Allowed types: {', '.join(sorted(ALLOWED_CLUSTER_TYPES))}"
        )

    galaxy_elements = data.get("GalaxyElement")
    meta = data.get("meta")

    if galaxy_elements is not None and not isinstance(galaxy_elements, list):
        raise ValueError("Field 'GalaxyElement' must be a list if provided.")

    if meta is not None and not isinstance(meta, dict):
        raise ValueError("Field 'meta' must be a dictionary/object if provided.")

    authors = data.get("authors", [])
    if authors is not None and not isinstance(authors, list):
        raise ValueError("Field 'authors' must be a list if provided.")

def meta_to_galaxy_elements(meta: dict[str, Any]) -> list[dict[str, str]]:
    elements: list[dict[str, str]] = []

    for key, value in meta.items():
        if isinstance(value, list):
            for item in value:
                elements.append({
                    "key": str(key),
                    "value": str(item),
                })
        else:
            elements.append({
                "key": str(key),
                "value": str(value),
            })

    return elements

def build_cluster_payload(data: dict[str, Any]) -> dict[str, Any]:
    value = str(data["value"]).strip()
    cluster_type = str(data["type"]).strip()

    payload: dict[str, Any] = {
        "value": value,
        "type": cluster_type,
        "description": str(data["description"]).strip(),
        "source": str(data.get("source", "internal")).strip(),
        "authors": data.get("authors", []),
        "distribution": int(data.get("distribution", 0)),
        "sharing_group_id": int(data.get("sharing_group_id", 0)),
        "tag_name": f'misp-galaxy:{cluster_type}="{value}"',
    }

    # Prefer explicit GalaxyElement if provided
    galaxy_elements = data.get("GalaxyElement")
    if galaxy_elements:
        payload["GalaxyElement"] = galaxy_elements
    else:
        meta = data.get("meta", {})
        if meta:
            payload["GalaxyElement"] = meta_to_galaxy_elements(meta)

    return payload

def import_cluster_from_file(misp, path: str):
    data = load_cluster_json(path)
    validate_cluster_data(data)
    payload = build_cluster_payload(data)

    galaxy = get_galaxy_by_type(misp, payload["type"])

    return misp.add_galaxy_cluster(
        galaxy=galaxy["id"],   # or galaxy["uuid"]
        galaxy_cluster=payload,
    )

def import_clusters_from_folder(misp, folder_path: str) -> dict[str, Any]:
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not folder.is_dir():
        raise ValueError(f"Path is not a folder: {folder_path}")

    json_files = sorted(folder.glob("*.json"))

    if not json_files:
        return {
            "folder": str(folder),
            "total": 0,
            "success_count": 0,
            "failure_count": 0,
            "results": [],
        }

    results: list[dict[str, Any]] = []
    success_count = 0
    failure_count = 0

    for json_file in json_files:
        try:
            result = import_cluster_from_file(misp, str(json_file))
            results.append({
                "file": json_file.name,
                "status": "success",
                "result": result,
            })
            success_count += 1
        except Exception as e:
            results.append({
                "file": json_file.name,
                "status": "error",
                "error": str(e),
            })
            failure_count += 1

    return {
        "folder": str(folder),
        "total": len(json_files),
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
    }