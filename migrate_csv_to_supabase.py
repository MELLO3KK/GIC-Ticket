"""
One-time migration script: uploads data from users.csv and tickets.csv to Supabase.
Run this once before starting the app with Supabase backend.

Usage:
    python migrate_csv_to_supabase.py
"""
import csv
import os
from supabase import create_client

SUPABASE_URL = "https://taiuvdmywepyudlpphnl.supabase.co"
SUPABASE_KEY = "sb_publishable_3BCU041TVAeBVEOIrmEVsA_6QgfEd8r"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_CSV = os.path.join(BASE_DIR, "users.csv")
TICKETS_CSV = os.path.join(BASE_DIR, "tickets.csv")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def migrate_users():
    if not os.path.exists(USERS_CSV):
        print("users.csv not found, skipping.")
        return

    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "username": row["username"],
                "token": str(row["token"]),
                "role": row["role"],
                "paid_amount": int(float(row.get("paid_amount", 0))),
            })

    if rows:
        res = supabase.table("users").upsert(rows, on_conflict="username").execute()
        print(f"Uploaded {len(rows)} users to Supabase.")
    else:
        print("No user rows found in CSV.")


def migrate_tickets():
    if not os.path.exists(TICKETS_CSV):
        print("tickets.csv not found, skipping.")
        return

    with open(TICKETS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "id": row["id"],
                "student_name": row["student_name"],
                "class_name": row["class_name"],
                "agent_username": row["agent_username"],
                "qr_token": row["qr_token"],
                "qr_image": row["qr_image"],
            })

    if rows:
        res = supabase.table("tickets").upsert(rows, on_conflict="id").execute()
        print(f"Uploaded {len(rows)} tickets to Supabase.")
    else:
        print("No ticket rows found in CSV.")


if __name__ == "__main__":
    print("Starting CSV -> Supabase migration...")
    migrate_users()
    migrate_tickets()
    print("Migration complete!")
