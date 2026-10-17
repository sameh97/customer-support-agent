"""
Staff CLI for tickets (stand-in for a helpdesk UI).

  docker compose exec app python -m scripts.manage_tickets list
  docker compose exec app python -m scripts.manage_tickets update T-7K2M9Q in_progress --note "Looking into it"
"""

import argparse

from src.tickets import STATUSES, list_all_tickets, update_ticket


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage support tickets")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="show recent tickets")

    update = sub.add_parser("update", help="change a ticket's status and/or note")
    update.add_argument("code")
    update.add_argument("status", nargs="?", choices=list(STATUSES))
    update.add_argument("--note", help="latest update the customer will see")

    args = parser.parse_args()

    if args.command == "list":
        for t in list_all_tickets():
            print(f"{t.code}  {t.status:<20} {t.created_at:%Y-%m-%d %H:%M}  {t.summary[:60]}")
    else:
        ticket = update_ticket(args.code, args.status, args.note)
        print(f"Updated {ticket.code}: {ticket.status}" if ticket else f"No ticket {args.code}")


if __name__ == "__main__":
    main()
