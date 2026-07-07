"""
Seeds sample AI Agent Document records for the 10 default ERPNext agents,
matching the exact doctype breakdown: Internal (General), Accounts,
Buying, Selling, CRM, HR, Manufacturing, Project, Stock, Support.

AI Agent Document isn't shipped as a fixture (unlike AI Agent and Router
Training Example) because inserting it triggers embedding into ChromaDB,
which needs the embedding model available -- better to run explicitly
after the app + its Python dependencies are fully installed.

Run once after `bench install-app frappe_ai` and `bench migrate`:
    bench --site <site> execute frappe_ai.setup.seed_sample_data.run
"""

import frappe

SAMPLE_DOCS = {
    "Internal": [
        "A Company record is the top-level entity in ERPNext; all transactions, accounts, and reports are scoped to a specific Company.",
        "A Warehouse represents a physical or virtual stock location; every stock transaction references a source and/or target Warehouse.",
        "An Item is the master record for anything bought, sold, or stocked -- it defines UOM, item group, valuation method, and default warehouse.",
        "An Address record can be linked to a Customer, Supplier, Company, or Contact, and supports multiple addresses per linked party.",
        "A Contact record stores a person's details (phone, email, designation) and can be linked to one or more Customers, Suppliers, or Leads.",
        "Email Accounts configure outgoing/incoming mail servers used for sending documents and, when linked, for auto-creating Communications or Tickets.",
        "Item Groups organize Items into a hierarchy, used for reporting, pricing rules, and default account/warehouse settings.",
        "A Company's default currency, fiscal year, and Chart of Accounts template are set at creation and affect every transaction under it.",
        "Multiple Companies can exist on one site, each with fully separate accounting, stock, and reporting, useful for group structures.",
        "Item Attributes and Variants let one template Item generate multiple sellable variations (e.g. size, color) without duplicating master data.",
    ],
    "Accounts": [
        "A Journal Entry is used to post manual accounting transactions such as adjustments, provisions, or opening balances directly between ledger accounts.",
        "A Payment Entry records money received from a customer or paid to a supplier and can be reconciled against one or more outstanding invoices.",
        "The Account doctype (Chart of Accounts) defines the tree of ledger accounts -- Assets, Liabilities, Income, Expense, Equity -- used across all transactions.",
        "A Sales Invoice bills a customer for goods or services delivered; a Purchase Invoice records a supplier's bill for goods or services received.",
        "An Asset record tracks a purchased fixed asset's cost, location, and depreciation details; Asset Depreciation entries reduce its book value over its useful life per a chosen schedule.",
        "Cost Centers allow tracking income and expense by department, project, or branch, independent of the Chart of Accounts structure.",
        "The General Ledger report shows every posted transaction against every account and is the primary tool for auditing financial entries.",
        "The Profit & Loss Statement summarizes income and expense accounts over a period to show net profit or loss.",
        "The Balance Sheet shows assets, liabilities, and equity as of a specific date, and must always balance (Assets = Liabilities + Equity).",
        "Depreciation methods (Straight Line or Written Down Value) determine how an Asset's value reduces each period on its Asset Depreciation schedule.",
    ],
    "Buying": [
        "A Supplier record stores vendor details, payment terms, and default currency used across all purchase transactions with them.",
        "A Material Request (type Purchase) is the standard trigger for procurement, raised manually or automatically from low stock levels.",
        "A Request for Quotation (RFQ) is sent to multiple suppliers to gather pricing before deciding on a Purchase Order.",
        "A Supplier Quotation records a supplier's response to an RFQ and can be directly compared against other suppliers' quotations.",
        "A Purchase Order is created from an approved Material Request or Supplier Quotation, confirming quantities, rates, and delivery dates.",
        "A Purchase Receipt is created when goods physically arrive, updating stock quantities before the Purchase Invoice is booked.",
        "The Purchase Analytics report breaks down spend by supplier, item, or item group over a selected date range.",
        "Purchase Order approval workflows can require manager sign-off above a configured amount before the order is submitted to the supplier.",
        "A Blanket Purchase Order sets an agreed quantity and rate with a supplier over a period, against which individual Purchase Orders are released.",
        "Landed Cost Vouchers allocate additional costs like freight and customs duty across received items on a Purchase Receipt for accurate valuation.",
    ],
    "Selling": [
        "A Customer record stores billing details, credit limit, and default price list used across all sales transactions with them.",
        "A Quotation is a non-binding offer sent to a prospective or existing customer, convertible into a Sales Order once accepted.",
        "A Sales Order confirms a customer's order details (items, quantities, rates, delivery date) and is the basis for delivery and invoicing.",
        "A Pick List consolidates items needed to fulfill one or more Sales Orders into a single warehouse picking task before delivery.",
        "A Delivery Note records goods physically shipped to a customer, generated directly or from a completed Pick List.",
        "Pricing Rules apply automatic discounts or price overrides based on customer, customer group, item, quantity, or date range conditions.",
        "Customer credit limits, when set, block new Sales Orders or Invoices once a customer's outstanding balance crosses the configured threshold.",
        "Sales Order fulfillment status tracks how much of an order has been picked, delivered, and invoiced versus what remains pending.",
        "A Sales Return is processed as a Sales Invoice with 'Is Return' checked, referencing the original invoice to reverse the transaction.",
        "Territory and Customer Group fields let sales data be sliced by region or customer segment in analytics reports.",
    ],
    "CRM": [
        "A Lead represents an unqualified prospect and is the entry point into the CRM pipeline before any real sales conversation has occurred.",
        "An Enquiry captures an inbound question or interest (often from a website form) before it's qualified into a Lead or Deal.",
        "A Deal (the CRM equivalent of a qualified prospect being actively pursued) tracks probability of closing, expected value, and pipeline stage.",
        "Converting a Lead into a Deal marks it as a qualified prospect actively being pursued for a specific sale.",
        "A Quotation can be generated directly from a Deal once terms are discussed, moving the prospect toward a formal Sales Order.",
        "Lead Sources (website, referral, campaign, cold call) are tracked to measure which channels generate the most qualified pipeline.",
        "Communication logs (calls, emails) attached to a Lead or Deal give the full history of interactions with a prospect.",
        "Lost Deals are marked with a lost reason, which feeds into reporting on why deals fail to close.",
        "Territory-based lead assignment automatically routes new leads to the right sales person based on region rules.",
        "The CRM pipeline / sales funnel report visualizes how many leads and deals exist at each stage, highlighting where prospects stall.",
    ],
    "HR": [
        "An Employee record is the master data for a staff member, linking to attendance, leave, payroll, and appraisal records.",
        "A Leave Application is submitted by an employee against a Leave Type and is approved by their reporting manager before leave is deducted.",
        "A Salary Structure defines the earning and deduction components (basic pay, allowances, taxes) that make up a role's compensation.",
        "A Salary Structure Assignment links a specific Employee to a Salary Structure with an effective-from date, so pay changes are versioned over time.",
        "A Shift Type defines working hours and attendance rules (like grace period for late check-in) for a category of work schedule.",
        "A Shift Type Assignment links a specific Employee to a Shift Type over a date range, supporting rotating or fixed shift patterns.",
        "The Holiday List defines company or location-specific non-working days, which affect attendance and leave calculations.",
        "A Salary Slip is generated per employee per payroll period based on their current Salary Structure Assignment.",
        "Appraisal Cycles collect structured performance feedback from managers and peers over a defined review period.",
        "Employee Onboarding uses a checklist-driven process to track document collection, asset assignment, and orientation tasks for new hires.",
    ],
    "Manufacturing": [
        "A Bill of Materials (BOM) defines the raw materials, quantities, and Operations required to manufacture one unit of a finished item.",
        "A Work Order is created from a BOM and tracks the manufacturing of a specific quantity of an item, including material and operation status.",
        "Job Cards track the execution of individual Operations within a Work Order, including time logs and operator assignment.",
        "An Operation defines a single manufacturing step (e.g. cutting, assembly, painting) referenced by a BOM's routing and executed via Job Cards.",
        "Stock Entry type 'Manufacture' records the consumption of raw materials and receipt of the finished item when a Work Order completes.",
        "Stock Entry type 'Material Transfer for Manufacturing' moves raw materials from a source warehouse to a work-in-progress warehouse before production starts.",
        "A Production Plan aggregates demand from Sales Orders or forecasts to determine what needs to be manufactured and by when.",
        "Routing defines the sequence of Operations (and the workstations they run on) that a BOM's manufacturing process follows.",
        "Multi-level BOMs reference other BOMs as sub-assemblies, allowing complex products to be broken into manageable manufacturing stages.",
        "Backflushing automatically consumes raw materials from stock based on the BOM when a Work Order's manufacture is completed, without manual stock entries.",
    ],
    "Projects": [
        "A Task is a unit of work, optionally linked to a Project, with dependencies, assignees, priority, and expected start/end dates.",
        "A Timesheet logs hours worked against specific Tasks and is the basis for billing time-and-materials clients or tracking effort.",
        "Task dependencies let one Task block or be blocked by another, visualized in a Gantt chart view.",
        "Billable vs non-billable hours are distinguished on a Timesheet to separate client-chargeable work from internal effort.",
        "A Timesheet can be submitted for approval before its hours are considered final for billing or reporting purposes.",
        "Task priority and status (Open, Working, Completed, Cancelled) drive how work is tracked and surfaced in project views.",
        "An invoice can be generated directly from approved Timesheet entries for time-and-materials billing arrangements.",
        "Task assignment lets a specific Task be delegated to a team member, who is then notified and accountable for its completion.",
        "Project-level reports aggregate Task completion and Timesheet hours to show overall progress and effort distribution.",
        "Recurring Tasks can be set up for repeating work items, so they don't need to be manually recreated each cycle.",
    ],
    "Stock": [
        "A Stock Entry records material movement -- transfers, receipts, issues, or manufacturing consumption -- and updates the Stock Ledger.",
        "Stock Entry type 'Material Transfer' moves stock between two warehouses without changing overall on-hand quantity.",
        "Stock Entry type 'Material Receipt' brings new stock into the system without a corresponding Purchase Receipt (e.g. found stock, opening stock).",
        "Stock Entry type 'Material Issue' removes stock from the system for consumption not tied to a sale (e.g. internal use, samples, write-off).",
        "The Stock Balance report shows current on-hand quantity and valuation for every item across every warehouse as of a selected date.",
        "Stock Reconciliation adjusts system quantities to match a physical count, and is the standard tool for correcting inventory discrepancies.",
        "Batch tracking groups stock by manufacturing batch (useful for expiry dates), while Serial Number tracking tracks individual units.",
        "The Stock Ledger report is the definitive, transaction-level record of every stock movement for an item across all warehouses.",
        "Reorder levels and reorder quantities, set per item per warehouse, can automatically trigger Material Requests when stock runs low.",
        "Stock valuation methods (FIFO or Moving Average) determine how the cost of goods sold is calculated as stock moves.",
    ],
    "Support": [
        "An HD Ticket is the core record in the Helpdesk app for a support request, tracking status, priority, assigned agent, and communication history.",
        "An SLA (Service Level Agreement) policy defines response and resolution time targets based on ticket priority or customer type.",
        "Canned Responses let support agents insert pre-written replies for common questions to speed up response time.",
        "Knowledge Base articles let customers self-serve answers to common questions before or instead of raising an HD Ticket.",
        "Ticket escalation rules automatically reassign or flag HD Tickets that breach their SLA response or resolution time.",
        "A 'permission error' in Frappe usually means the user's Role doesn't have the required permission level on that DocType -- check Role Permissions Manager.",
        "A 'duplicate entry' error typically means a unique field (like a naming series value) collided -- check for an existing record with the same ID.",
        "Clearing the cache (bench clear-cache) resolves many stale-data issues after code or configuration changes.",
        "Background job failures can be inspected under 'Background Jobs' in the Desk, or via bench --site <site> show-pending-jobs from the CLI.",
        "A failed migration should be diagnosed via the bench error log before retrying bench migrate, since re-running blind can mask the root cause.",
    ],
}


def run():
    created = 0
    for agent_key, docs in SAMPLE_DOCS.items():
        if not frappe.db.exists("AI Agent", agent_key):
            print(f"Skipping '{agent_key}' -- no AI Agent record with that key exists.")
            continue
        for content in docs:
            frappe.get_doc(
                {"doctype": "AI Agent Document", "agent": agent_key, "content": content}
            ).insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    print(f"Seeded {created} sample knowledge base documents across {len(SAMPLE_DOCS)} agents.")
