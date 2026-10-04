from typing import Any

class EventProcessor:
    def __init__(self, misp_client, repo, scorer, notifier, config: dict[str, Any]):
        self.misp_client = misp_client
        self.repo = repo
        self.scorer = scorer
        self.notifier = notifier
        self.config = config