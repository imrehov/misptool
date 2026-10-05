import urllib3
from typing import Any, Dict

from pymisp import PyMISP


class MispClient:

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.misp_client = self.__build_misp_client()

    def fetch_events(self, lookback_minutes: int) -> list[dict[str, Any]]:
        return self.misp_client.search(
            controller="events",
            timestamp=f"{lookback_minutes}m",
            pythonify=False,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self.misp_client, name)

    def __build_misp_client(self) -> PyMISP:
        misp_cfg = self.config.get("misp", {})

        url = misp_cfg.get("url")
        key = misp_cfg.get("key")
        verify_ssl = misp_cfg.get("verify_ssl", True)

        if not url:
            raise ValueError("Missing config: misp.url")
        if not key:
            raise ValueError("Missing config: misp.key")

        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return PyMISP(url, key, ssl=verify_ssl)
