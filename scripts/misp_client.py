import urllib3
from typing import Any, Dict

from pymisp import PyMISP


def build_misp_client(config: Dict[str, Any]) -> PyMISP:
    misp_cfg = config.get("misp", {})

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