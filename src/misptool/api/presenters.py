def present_event_state(event: dict, misp_url: str) -> dict:
    return {
        **event,
        "misp_event_url": f"{misp_url.rstrip('/')}/events/view/{event['event_id']}",
    }