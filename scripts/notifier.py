import requests
from typing import Any


def build_event_url(event_id: str, misp_url: str) -> str:
    return f"{misp_url.rstrip('/')}/events/view/{event_id}"


def format_discord_message(summary: dict[str, Any], misp_url: str, config: dict[str, Any]) -> str:
    event_id = summary.get("id")
    info = summary.get("info", "No title")
    score = summary.get("score", 0)
    change_reason = str(summary.get("change_reason", "update")).lower()
    change_summary = summary.get("change_summary", [])

    discord_user_to_ping = "add a userid to config for pings"
    notifications_cfg = config.get("notifications", {})
    discord_user_to_ping = notifications_cfg.get("discord_userid")


    attribute_count = summary.get("attribute_count", 0)
    object_count = summary.get("object_count", 0)
    tag_count = summary.get("tag_count", 0)
    galaxy_tag_count = summary.get("galaxy_tag_count", 0)

    url = build_event_url(str(event_id), misp_url)

    if change_reason == "new":
        reason_str = "🆕 NEW EVENT"
    elif change_reason == "enriched":
        reason_str = "🧠 ENRICHED EVENT"
    else:
        reason_str = "🔄 UPDATED EVENT"

    message = (
        f"{discord_user_to_ping} \n"
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
    summary: dict[str, Any],
    webhook_url: str,
    misp_url: str,
) -> None:
    message = format_discord_message(summary, misp_url)

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=10,
    )

    if response.status_code >= 400:
        print("Discord notification failed:", response.text)


def notify_console(summary: dict[str, Any]) -> None:
    print("\n=== EVENT ALERT ===")
    for key, value in summary.items():
        print(f"{key}: {value}")