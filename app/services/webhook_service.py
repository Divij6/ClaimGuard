from app.db.supabase import supabase


def event_already_processed(stripe_event_id: str) -> bool:
    response = (
        supabase
        .table("webhook_events")
        .select("status")
        .eq("stripe_event_id", stripe_event_id)
        .execute()
    )

    if not response.data:
        return False

    return response.data[0]["status"] == "processed"

def mark_webhook_processed(stripe_event_id: str):
    response = (
        supabase
        .table("webhook_events")
        .update({"status": "processed"})
        .eq("stripe_event_id", stripe_event_id)
        .execute()
    )

    return response.data[0]

def record_webhook_event(
    stripe_event_id: str,
    event_type: str,
):
    response = (
        supabase
        .table("webhook_events")
        .insert(
            {
                "stripe_event_id": stripe_event_id,
                "event_type": event_type,
            }
        )
        .execute()
    )

    return response.data[0]