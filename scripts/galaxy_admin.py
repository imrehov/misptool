import uuid
from typing import Any

import requests


def list_galaxies(misp) -> list[dict[str, Any]]:
    galaxies = misp.galaxies(pythonify=False)

    if isinstance(galaxies, dict) and "response" in galaxies:
        galaxies = galaxies["response"]

    normalized: list[dict[str, Any]] = []
    for item in galaxies:
        galaxy = item.get("Galaxy", item)
        normalized.append(galaxy)

    return normalized


def find_galaxy_by_type(misp, galaxy_type: str) -> dict[str, Any] | None:
    for galaxy in list_galaxies(misp):
        if str(galaxy.get("type", "")).strip() == galaxy_type:
            return galaxy
    return None


def build_galaxy_payload(
    name: str,
    galaxy_type: str,
    description: str,
    namespace: str = "custom",
    icon: str = "user-secret",
    version: int = 1,
) -> dict[str, Any]:
    return {
        "uuid": str(uuid.uuid4()),
        "name": name,
        "type": galaxy_type,
        "description": description,
        "namespace": namespace,
        "version": version,
        "icon": icon,
        "enabled": True,
    }


def create_galaxy(
    misp,
    name: str,
    galaxy_type: str,
    description: str,
    namespace: str = "custom",
    icon: str = "user-secret",
) -> Any:
    payload = build_galaxy_payload(
        name=name,
        galaxy_type=galaxy_type,
        description=description,
        namespace=namespace,
        icon=icon,
    )

    headers = {
        "Authorization": misp.key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{misp.root_url}/galaxies/add",
        headers=headers,
        json=payload,
        verify=misp.ssl,
        timeout=30,
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    if response.status_code >= 400:
        raise RuntimeError(f"Galaxy creation failed ({response.status_code}): {data}")

    return data


def ensure_galaxy(
    misp,
    name: str,
    galaxy_type: str,
    description: str,
    namespace: str = "custom",
    icon: str = "user-secret",
) -> dict[str, Any]:
    existing = find_galaxy_by_type(misp, galaxy_type)
    if existing:
        return {
            "status": "exists",
            "galaxy": existing,
        }

    created = create_galaxy(
        misp=misp,
        name=name,
        galaxy_type=galaxy_type,
        description=description,
        namespace=namespace,
        icon=icon,
    )
    return {
        "status": "created",
        "galaxy": created,
    }