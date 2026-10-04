import requests

from typing import Dict, Any

class Notifier:

    def __init__(self, config: Dict[str, Any]):
        self.misp_url = config.get("misp", {}).get("url", {})
        self.ntf_config = config.get("notifications", {})
        self.discord_user_to_ping = self.ntf_config.get("discord_userid", {})
        self.discord_webhook = self.ntf_config.get("discord_webhook", {})

    def build_event_url(self, event_id: str) -> str:
        return f"{self.misp_url.rstrip('/')}/events/view/{event_id}"


    def format_discord_message(self, summary: dict[str, Any]) -> str:
        event_id = summary.get("id")
        info = summary.get("info", "No title")
        score = summary.get("score", 0)
        change_reason = str(summary.get("change_reason", "update")).lower()
        change_summary = summary.get("change_summary", [])

        #discord_user_to_ping = "<@210454721872396288>" # fix this later
        # notifications_cfg = config.get("notifications", {})
        # discord_user_to_ping = notifications_cfg.get("discord_userid")


        attribute_count = summary.get("attribute_count", 0)
        object_count = summary.get("object_count", 0)
        tag_count = summary.get("tag_count", 0)
        galaxy_tag_count = summary.get("galaxy_tag_count", 0)

        url = self.build_event_url(str(event_id))

        if change_reason == "new":
            reason_str = "🆕 NEW EVENT"
        elif change_reason == "enriched":
            reason_str = "🧠 ENRICHED EVENT"
        else:
            reason_str = "🔄 UPDATED EVENT"

        message = (
            f"{self.discord_user_to_ping} \n"
            f"**{reason_str}**\n"
            f"**Score:** {score}\n\n"
            f"**{info}**\n\n"
            f"**Event ID:** `{event_id}`\n"
            f"**Attributes:** {attribute_count} | **Objects:** {object_count}\n"
            f"**Tags:** {tag_count} | **Galaxy Tags:** {galaxy_tag_count}\n\n"
            f"🔗 {url}"
        )

        if change_summary:
            diff_lines = []
            for line in change_summary:
                if "added" in line or "-> True" in line:
                    diff_lines.append(f"+ {line}")
                elif "removed" in line or "-> False" in line:
                    diff_lines.append(f"- {line}")
                else:
                    diff_lines.append(f"! {line}")

            message += "\n```diff\n" + "\n".join(diff_lines) + "\n```"

        return message


    def notify_discord(
        self,
        summary: dict[str, Any],
    ) -> None:
        if not self.discord_webhook:
            return
        message = self.format_discord_message(summary, self.misp_url, self.discord_user_to_ping)

        response = requests.post(
            self.discord_webhook,
            json={"content": message},
            timeout=10,
        )

        if response.status_code >= 400:
            print("Discord notification failed:", response.text)


    def notify_console(self, summary: dict[str, Any]) -> None:
        print("\n=== EVENT ALERT ===")
        for key, value in summary.items():
            print(f"{key}: {value}")