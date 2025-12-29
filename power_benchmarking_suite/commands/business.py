"""
Business Command - Client management, invoices, check-ins, and workflows

Usage:
    power-benchmark business clients list
    power-benchmark business clients create --name "Name" --email email@example.com
    power-benchmark business invoices create --client-id xxx --amount 199.00
    power-benchmark business workflows run-checkins
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Import business modules
from ..business import (
    ClientManager,
    ClientStatus,
    InvoiceManager,
    CheckinManager,
    OnboardingManager,
    WorkflowManager,
)

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add business command to argument parser."""
    parser = subparsers.add_parser(
        "business",
        aliases=["biz"],
        help="Business automation (clients, invoices, check-ins, workflows)",
        description="Manage clients, invoices, check-ins, and automated workflows",
    )

    subparsers_biz = parser.add_subparsers(dest="business_type", help="Business operation type")

    # Clients subcommand
    parser_clients = subparsers_biz.add_parser(
        "clients", help="Client management", description="Create, list, update, and delete clients"
    )
    parser_clients.add_argument(
        "action", choices=["list", "get", "create", "update", "delete"], help="Action to perform"
    )
    parser_clients.add_argument("--id", type=str, help="Client ID")
    parser_clients.add_argument("--email", type=str, help="Client email")
    parser_clients.add_argument("--name", type=str, help="Contact name")
    parser_clients.add_argument("--company", type=str, help="Company name")
    parser_clients.add_argument("--phone", type=str, help="Contact phone")
    parser_clients.add_argument(
        "--status",
        type=str,
        choices=["prospect", "onboarding", "active", "inactive", "churned"],
        help="Client status",
    )
    parser_clients.add_argument("--monthly-fee", type=float, help="Monthly fee")
    parser_clients.set_defaults(business_subtype="clients")

    # Invoices subcommand
    parser_invoices = subparsers_biz.add_parser(
        "invoices", help="Invoice management", description="Create, list, and manage invoices"
    )
    parser_invoices.add_argument(
        "action", choices=["list", "get", "create", "mark-paid", "delete"], help="Action to perform"
    )
    parser_invoices.add_argument("--id", type=str, help="Invoice ID")
    parser_invoices.add_argument("--client-id", type=str, help="Client ID")
    parser_invoices.add_argument("--amount", type=float, help="Invoice amount")
    parser_invoices.add_argument("--description", type=str, help="Invoice description")
    parser_invoices.add_argument("--generate-pdf", action="store_true", help="Generate PDF invoice")
    parser_invoices.set_defaults(business_subtype="invoices")

    # Check-ins subcommand
    parser_checkins = subparsers_biz.add_parser(
        "checkins", help="Check-in management", description="Manage monthly check-ins"
    )
    parser_checkins.add_argument(
        "action", choices=["list", "due", "create"], help="Action to perform"
    )
    parser_checkins.add_argument("--client-id", type=str, help="Client ID")
    parser_checkins.add_argument("--notes", type=str, help="Check-in notes")
    parser_checkins.set_defaults(business_subtype="checkins")

    # Workflows subcommand
    parser_workflows = subparsers_biz.add_parser(
        "workflows", help="Workflow automation", description="Run automated workflows"
    )
    parser_workflows.add_argument(
        "action", choices=["run-checkins", "run-reminders"], help="Workflow to run"
    )
    parser_workflows.add_argument("--no-email", action="store_true", help="Skip sending emails")
    parser_workflows.set_defaults(business_subtype="workflows")

    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute business command."""
    try:
        if not hasattr(args, "business_type") or args.business_type is None:
            logger.error(
                "Business operation type required. Use 'clients', 'invoices', 'checkins', or 'workflows'"
            )
            return 1

        if args.business_type == "clients":
            return _handle_clients(args, config)
        elif args.business_type == "invoices":
            return _handle_invoices(args, config)
        elif args.business_type == "checkins":
            return _handle_checkins(args, config)
        elif args.business_type == "workflows":
            return _handle_workflows(args, config)
        else:
            logger.error(f"Unknown business type: {args.business_type}")
            return 1

    except Exception as e:
        logger.error(f"Business command failed: {e}", exc_info=True)
        return 1


def _handle_clients(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle client operations."""
    manager = ClientManager()

    if args.action == "list":
        clients = manager.list_clients()
        print(f"\nFound {len(clients)} clients:\n")
        for client in clients:
            print(f"  ID: {client.get('id')}")
            print(f"  Company: {client.get('company')}")
            print(
                f"  Contact: {client.get('contact', {}).get('name')} <{client.get('contact', {}).get('email')}>"
            )
            print(f"  Status: {client.get('status')}")
            print()
        return 0

    elif args.action == "get":
        if args.id:
            client = manager.get_client(args.id)
        elif args.email:
            client = manager.get_client_by_email(args.email)
        else:
            logger.error("--id or --email required for 'get' action")
            return 1

        if not client:
            logger.error("Client not found")
            return 1

        print(f"\nClient Details:")
        print(f"  ID: {client.get('id')}")
        print(f"  Company: {client.get('company')}")
        print(
            f"  Contact: {client.get('contact', {}).get('name')} <{client.get('contact', {}).get('email')}>"
        )
        print(f"  Status: {client.get('status')}")
        print(f"  Monthly Fee: ${client.get('monthlyFee', 0):.2f}")
        return 0

    elif args.action == "create":
        if not args.name or not args.email:
            logger.error("--name and --email required for 'create' action")
            return 1

        client = manager.create_client(
            company=args.company or args.name,
            contact_name=args.name,
            contact_email=args.email,
            contact_phone=args.phone,
            monthly_fee=args.monthly_fee or 297.0,
            status=args.status or ClientStatus.ONBOARDING,
        )

        print(f"\n✅ Client created:")
        print(f"  ID: {client.get('id')}")
        print(f"  Company: {client.get('company')}")
        print(f"  Email: {client.get('contact', {}).get('email')}")
        return 0

    elif args.action == "update":
        if not args.id:
            logger.error("--id required for 'update' action")
            return 1

        updates = {}
        if args.status:
            updates["status"] = args.status
        if args.monthly_fee:
            updates["monthlyFee"] = args.monthly_fee

        if not updates:
            logger.error("No updates specified. Use --status or --monthly-fee")
            return 1

        client = manager.update_client(args.id, updates)
        if not client:
            logger.error("Client not found")
            return 1

        print(f"\n✅ Client updated: {args.id}")
        return 0

    elif args.action == "delete":
        if not args.id:
            logger.error("--id required for 'delete' action")
            return 1

        if manager.delete_client(args.id):
            print(f"\n✅ Client deleted: {args.id}")
            return 0
        else:
            logger.error("Client not found")
            return 1

    return 1


def _handle_invoices(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle invoice operations."""
    manager = InvoiceManager()

    if args.action == "list":
        invoices = manager.list_invoices()
        print(f"\nFound {len(invoices)} invoices:\n")
        for invoice in invoices:
            print(f"  ID: {invoice.get('id')}")
            print(f"  Client ID: {invoice.get('clientId')}")
            print(f"  Amount: ${invoice.get('amount', 0):.2f}")
            print(f"  Status: {invoice.get('status')}")
            print()
        return 0

    elif args.action == "get":
        if not args.id:
            logger.error("--id required for 'get' action")
            return 1

        invoice = manager.get_invoice(args.id)
        if not invoice:
            logger.error("Invoice not found")
            return 1

        print(f"\nInvoice Details:")
        print(f"  ID: {invoice.get('id')}")
        print(f"  Client ID: {invoice.get('clientId')}")
        print(f"  Amount: ${invoice.get('amount', 0):.2f}")
        print(f"  Status: {invoice.get('status')}")
        print(f"  Due Date: {invoice.get('dueDate')}")
        return 0

    elif args.action == "create":
        if not args.client_id or not args.amount:
            logger.error("--client-id and --amount required for 'create' action")
            return 1

        invoice = manager.create_invoice(
            client_id=args.client_id,
            amount=args.amount,
            description=args.description or "Monthly subscription",
        )

        print(f"\n✅ Invoice created:")
        print(f"  ID: {invoice.get('id')}")
        print(f"  Amount: ${invoice.get('amount', 0):.2f}")

        if args.generate_pdf:
            from ..services.pdf_generator import PDFGenerator
            from ..business.clients import ClientManager

            pdf_gen = PDFGenerator()
            client_manager = ClientManager()
            client = client_manager.get_client(args.client_id)

            if client:
                pdf_path = pdf_gen.generate_invoice(invoice, client)
                if pdf_path:
                    print(f"  PDF: {pdf_path}")

        return 0

    elif args.action == "mark-paid":
        if not args.id:
            logger.error("--id required for 'mark-paid' action")
            return 1

        invoice = manager.mark_paid(args.id)
        if not invoice:
            logger.error("Invoice not found")
            return 1

        print(f"\n✅ Invoice marked as paid: {args.id}")
        return 0

    elif args.action == "delete":
        if not args.id:
            logger.error("--id required for 'delete' action")
            return 1

        if manager.delete_invoice(args.id):
            print(f"\n✅ Invoice deleted: {args.id}")
            return 0
        else:
            logger.error("Invoice not found")
            return 1

    return 1


def _handle_checkins(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle check-in operations."""
    manager = CheckinManager()

    if args.action == "list":
        if args.client_id:
            checkins = manager.get_checkins_by_client(args.client_id)
            print(f"\nFound {len(checkins)} check-ins for client {args.client_id}:\n")
        else:
            logger.error("--client-id required for 'list' action")
            return 1

        for checkin in checkins:
            print(f"  Date: {checkin.get('date')}")
            print(f"  Notes: {checkin.get('notes', '')}")
            print()
        return 0

    elif args.action == "due":
        due_checkins = manager.get_due_checkins()
        print(f"\nFound {len(due_checkins)} clients due for check-ins:\n")
        for item in due_checkins:
            client = item["client"]
            print(f"  Client: {client.get('company')} ({client.get('id')})")
            print(f"  Days since last check-in: {item.get('daysSinceLastCheckin', 0)}")
            print()
        return 0

    elif args.action == "create":
        if not args.client_id:
            logger.error("--client-id required for 'create' action")
            return 1

        checkin = manager.create_checkin(
            client_id=args.client_id,
            notes=args.notes,
        )

        print(f"\n✅ Check-in created:")
        print(f"  Client ID: {checkin.get('clientId')}")
        print(f"  Date: {checkin.get('date')}")
        return 0

    return 1


def _handle_workflows(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle workflow operations."""
    manager = WorkflowManager()

    if args.action == "run-checkins":
        results = manager.run_checkins(send_emails=not args.no_email)
        print(f"\n✅ Check-in workflow complete:")
        print(f"  Total due: {results.get('total_due', 0)}")
        print(f"  Emails sent: {results.get('emails_sent', 0)}")
        if results.get("errors"):
            print(f"  Errors: {len(results.get('errors', []))}")
        return 0

    elif args.action == "run-reminders":
        results = manager.run_reminders(send_emails=not args.no_email)
        print(f"\n✅ Reminder workflow complete:")
        print(f"  Total reminders: {results.get('total_reminders', 0)}")
        print(f"  Emails sent: {results.get('emails_sent', 0)}")
        if results.get("errors"):
            print(f"  Errors: {len(results.get('errors', []))}")
        return 0

    return 1

