import os
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


def get_all_tokens():
    """Return list of all existing token strings."""
    res = supabase.table("users").select("token").execute()
    return [str(row["token"]) for row in res.data]


# ─── Tickets ──────────────────────────────────────────────────────────────────

def get_all_tickets():
    """Return list of ticket dicts."""
    res = supabase.table("tickets").select("*").execute()
    return res.data


def get_tickets_by_agent(username: str):
    """Return tickets created by a specific agent."""
    res = supabase.table("tickets").select("*").eq("agent_username", username).execute()
    return res.data


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
