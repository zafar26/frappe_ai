"""
Read-only tools the Accounts agent can call to look up LIVE ERPNext
data, instead of only answering from static RAG knowledge base text.

This is the reference implementation of the "agentic" pattern in
Frappe AI: the LLM decides, mid-conversation, whether it needs to call
one of these functions, reasons over the real result, and only then
answers. See agents/agentic_loop.py for the loop that drives this.

Safety boundary (not optional): every tool here goes through
frappe.get_list()/frappe.get_all() WITHOUT ignore_permissions, so a
user only ever sees data their own Frappe role already permits them to
see. Tools are read-only -- nothing here creates, edits, or deletes
any document.

To add tools for another agent: create tools/<agent>_tools.py with the
same TOOL_REGISTRY + TOOL_DESCRIPTIONS shape, then register it in
agents/agentic_loop.py's TOOL_REGISTRIES_BY_AGENT, and set
enable_tools=1 on that AI Agent record.
"""

import frappe


def _require_doctype(doctype: str):
    if not frappe.db.exists("DocType", doctype):
        raise Exception(
            f"The '{doctype}' DocType isn't installed on this site "
            "(is ERPNext installed here?)."
        )


def list_sales_invoices(customer: str = None, status: str = None, limit: int = 5):
    """Recent Sales Invoices, optionally filtered by customer name and status."""
    _require_doctype("Sales Invoice")
    filters = {}
    if customer:
        filters["customer"] = ["like", f"%{customer}%"]
    if status:
        filters["status"] = status

    return frappe.get_list(
        "Sales Invoice",
        filters=filters,
        fields=["name", "customer", "status", "grand_total", "outstanding_amount", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=min(int(limit or 5), 20),
    )


def list_purchase_invoices(supplier: str = None, status: str = None, limit: int = 5):
    """Recent Purchase Invoices, optionally filtered by supplier name and status."""
    _require_doctype("Purchase Invoice")
    filters = {}
    if supplier:
        filters["supplier"] = ["like", f"%{supplier}%"]
    if status:
        filters["status"] = status

    return frappe.get_list(
        "Purchase Invoice",
        filters=filters,
        fields=["name", "supplier", "status", "grand_total", "outstanding_amount", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=min(int(limit or 5), 20),
    )


def get_customer_outstanding(customer: str):
    """Total outstanding receivable amount across a customer's submitted Sales Invoices."""
    _require_doctype("Sales Invoice")
    if not customer:
        raise Exception("customer is required")

    result = frappe.db.sql(
        """
        SELECT customer,
               SUM(outstanding_amount) AS total_outstanding,
               COUNT(*) AS invoice_count
        FROM `tabSales Invoice`
        WHERE customer LIKE %s AND docstatus = 1
        GROUP BY customer
        """,
        (f"%{customer}%",),
        as_dict=True,
    )
    return result or [{"customer": customer, "total_outstanding": 0, "invoice_count": 0}]


def get_gl_entries(account: str, limit: int = 5):
    """Recent General Ledger entries for a given Account."""
    _require_doctype("GL Entry")
    if not account:
        raise Exception("account is required")

    return frappe.get_list(
        "GL Entry",
        filters={"account": ["like", f"%{account}%"]},
        fields=["account", "posting_date", "debit", "credit", "against", "voucher_type", "voucher_no"],
        order_by="posting_date desc",
        limit_page_length=min(int(limit or 5), 20),
    )


TOOL_REGISTRY = {
    "list_sales_invoices": list_sales_invoices,
    "list_purchase_invoices": list_purchase_invoices,
    "get_customer_outstanding": get_customer_outstanding,
    "get_gl_entries": get_gl_entries,
}

TOOL_DESCRIPTIONS = """
- list_sales_invoices(customer=None, status=None, limit=5): Recent Sales Invoices, optionally filtered by customer name and status (Draft, Unpaid, Paid, Overdue, Cancelled).
- list_purchase_invoices(supplier=None, status=None, limit=5): Recent Purchase Invoices, optionally filtered by supplier name and status.
- get_customer_outstanding(customer): Total outstanding receivable amount across a customer's Sales Invoices.
- get_gl_entries(account, limit=5): Recent General Ledger entries for a given Account.
""".strip()
