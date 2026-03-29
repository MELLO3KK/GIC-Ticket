import os
import datetime
from supabase import create_client, Client

SUPABASE_URL = "https://taiuvdmywepyudlpphnl.supabase.co"
SUPABASE_KEY = "sb_publishable_3BCU041TVAeBVEOIrmEVsA_6QgfEd8r"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Users ────────────────────────────────────────────────────────────────────

def get_user_by_token(token: str):
    """Return user dict or None."""
    res = supabase.table("users").select("*").eq("token", str(token)).execute()
    return res.data[0] if res.data else None


def get_user_by_username(username: str):
    """Return user dict or None."""
    res = supabase.table("users").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None


def get_all_users():
    """Return list of user dicts."""
    res = supabase.table("users").select("*").execute()
    return res.data


def create_user(username: str, token: str, role: str, paid_amount: int = 0):
    """Insert a new user row."""
    supabase.table("users").insert({
        "username": username,
        "token": token,
        "role": role,
        "paid_amount": paid_amount,
    }).execute()


def update_user_paid_amount(username: str, amount: int):
    """Set paid_amount for a user."""
    supabase.table("users").update({
        "paid_amount": amount,
    }).eq("username", username).execute()


def update_user_can_sell(username: str, can_sell: bool):
    """Set can_sell_tickets for a user."""
    supabase.table("users").update({
        "can_sell_tickets": can_sell,
    }).eq("username", username).execute()


def update_all_agents_can_sell(can_sell: bool):
    """Set can_sell_tickets for all agents."""
    supabase.table("users").update({
        "can_sell_tickets": can_sell,
    }).eq("role", "agent").execute()


def get_all_tokens():
    """Return list of all existing token strings."""
    res = supabase.table("users").select("token").execute()
    return [str(row["token"]) for row in res.data]


# ─── Tickets ──────────────────────────────────────────────────────────────────

def get_all_tickets():
    """Return list of ticket dicts, newest first (heuristic)."""
    res = supabase.table("tickets").select("*").execute()
    return res.data[::-1]


def get_tickets_by_agent(username: str):
    """Return tickets created by a specific agent, newest first (heuristic)."""
    res = supabase.table("tickets").select("*").eq("agent_username", username).execute()
    return res.data[::-1]


def get_ticket_by_id(ticket_id: str):
    """Return ticket dict or None."""
    res = supabase.table("tickets").select("*").eq("id", ticket_id).execute()
    return res.data[0] if res.data else None


def create_ticket(ticket: dict):
    """Insert a new ticket row."""
    supabase.table("tickets").insert(ticket).execute()


def update_ticket(ticket_id: str, updates: dict):
    """Update specified fields on a ticket."""
    supabase.table("tickets").update(updates).eq("id", ticket_id).execute()


def delete_ticket(ticket_id: str):
    """Delete a ticket by id."""
    supabase.table("tickets").delete().eq("id", ticket_id).execute()


def count_tickets_by_agent(username: str) -> int:
    """Return the number of tickets sold by an agent."""
    res = supabase.table("tickets").select("id", count="exact").eq("agent_username", username).execute()
    return res.count if res.count is not None else 0


def get_ticket_by_qr(qr_token: str):
    """Return ticket dict or None based on qr_token."""
    res = supabase.table("tickets").select("*").eq("qr_token", qr_token).execute()
    return res.data[0] if res.data else None


def log_attendance(ticket_id: str, student_name: str, event_type: str):
    """Log check-in or check-out event."""
    tz = datetime.timezone(datetime.timedelta(hours=6, minutes=30))
    timestamp = datetime.datetime.now(tz).isoformat()
    supabase.table("attendance_log").insert({
        "ticket_id": ticket_id,
        "student_name": student_name,
        "event_type": event_type,
        "timestamp": timestamp
    }).execute()
    return timestamp


def get_last_attendance(ticket_id: str):
    """Return the most recent attendance log entry for a ticket, or None."""
    res = (
        supabase.table("attendance_log")
        .select("*")
        .eq("ticket_id", ticket_id)
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_all_attendance():
    """Return all attendance log entries, newest first."""
    res = (
        supabase.table("attendance_log")
        .select("*")
        .order("timestamp", desc=True)
        .execute()
    )
    return res.data

