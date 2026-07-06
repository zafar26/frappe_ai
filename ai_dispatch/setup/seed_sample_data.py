"""
Seeds sample AI Agent Document records for the 11 default ERPNext-flavored
agents. AI Agent Document isn't shipped as a fixture (unlike AI Agent and
Router Training Example) because inserting it triggers embedding into
ChromaDB, which needs the embedding model available -- better to run
explicitly after the app + its Python dependencies are fully installed.

Run once after `bench install-app ai_dispatch` and `bench migrate`:
    bench --site <site> execute ai_dispatch.setup.seed_sample_data.run
"""

import frappe

SAMPLE_DOCS = {
    "accounts": [
        "A Journal Entry is used to post manual accounting transactions such as adjustments, provisions, or opening balances directly between ledger accounts.",
        "A Payment Entry records money received from a customer or paid to a supplier and can be reconciled against one or more outstanding invoices.",
        "The Chart of Accounts defines the tree of ledger accounts (Assets, Liabilities, Income, Expense, Equity) used across all accounting transactions.",
        "Fiscal Year defines the accounting period; it must be closed via a Period Closing Voucher before a new year's opening balances are posted.",
        "Tax Templates (Sales Taxes and Charges Template, Purchase Taxes and Charges Template) define default tax rules applied automatically to invoices.",
        "The General Ledger report shows every posted transaction against every account and is the primary tool for auditing financial entries.",
        "Cost Centers allow tracking income and expense by department, project, or branch, independent of the Chart of Accounts structure.",
        "Accounts Receivable and Accounts Payable aging reports show outstanding customer and supplier balances grouped by how overdue they are.",
        "Multi-currency accounting is enabled per account; exchange gain/loss is calculated automatically at the time of payment reconciliation.",
        "A Credit Note (Sales Invoice with is_return checked) reverses a sales invoice partially or fully, typically for returns or billing corrections.",
    ],
    "buying": [
        "A Purchase Order is created from an approved Material Request or directly, and confirms quantities, rates, and delivery dates with a supplier.",
        "A Request for Quotation (RFQ) is sent to multiple suppliers to compare pricing before creating a Purchase Order.",
        "A Purchase Receipt is created when goods physically arrive, and updates stock quantities before the Purchase Invoice is booked.",
        "Supplier Scorecards track delivery performance, quality, and pricing consistency to evaluate supplier reliability over time.",
        "A Blanket Purchase Order sets an agreed quantity and rate with a supplier over a period, against which individual Purchase Orders are released.",
        "Landed Cost Vouchers allocate additional costs like freight and customs duty across received items to get accurate item valuation.",
        "Material Requests of type Purchase are the standard trigger for procurement, often generated automatically from low stock levels.",
        "Purchase Order approval workflows can require manager sign-off above a configured amount before the order is submitted to the supplier.",
        "Subcontracting Purchase Orders send raw materials to a supplier who returns a finished or semi-finished product, tracked via a Subcontracting Order.",
        "The Purchase Analytics report breaks down spend by supplier, item, or item group over a selected date range.",
    ],
    "selling": [
        "A Sales Order confirms a customer's order details (items, quantities, rates, delivery date) and is the basis for delivery and invoicing.",
        "A Quotation is a non-binding offer sent to a prospective or existing customer, which can be converted into a Sales Order once accepted.",
        "Pricing Rules apply automatic discounts or price overrides based on customer, customer group, item, quantity, or date range conditions.",
        "A Delivery Note records goods physically shipped to a customer and reduces stock quantity independently of invoicing.",
        "Customer credit limits, when set, block new Sales Orders or Invoices once a customer's outstanding balance crosses the configured threshold.",
        "A Point of Sale (POS) Invoice is used for retail, walk-in-style sales and can print receipts and integrate with a cash/card payment flow.",
        "Sales Order fulfillment status tracks how much of an order has been delivered and invoiced versus what remains pending.",
        "Sales Partners and Sales Commission settings track referral-based sales and calculate commission payouts on invoiced amounts.",
        "Territory and Customer Group fields let sales data be sliced by region or customer segment in analytics reports.",
        "A Sales Return is processed as a Sales Invoice with 'Is Return' checked, referencing the original invoice to reverse the transaction.",
    ],
    "stock": [
        "A Stock Entry records material movement -- transfers between warehouses, issues, receipts, or manufacturing consumption -- and updates the Stock Ledger.",
        "Stock Reconciliation adjusts system quantities to match a physical count, and is the standard tool for correcting inventory discrepancies.",
        "Warehouses represent physical or virtual storage locations; stock quantity and valuation are always tracked per warehouse.",
        "Batch tracking groups stock by manufacturing batch (useful for expiry dates), while Serial Number tracking tracks individual units.",
        "The Stock Ledger report is the definitive, transaction-level record of every stock movement for an item across all warehouses.",
        "Reorder levels and reorder quantities, set per item per warehouse, can automatically trigger Material Requests when stock runs low.",
        "UOM (Unit of Measure) conversions let an item be bought in one unit (e.g. box) and sold or consumed in another (e.g. piece).",
        "Stock valuation methods (FIFO or Moving Average) determine how the cost of goods sold is calculated as stock moves.",
        "A Pick List consolidates items needed to fulfill one or more Sales Orders or Delivery Notes into a single warehouse picking task.",
        "Putaway Rules automatically suggest which warehouse/bin newly received stock should be placed into based on configured priorities.",
    ],
    "manufacturing": [
        "A Bill of Materials (BOM) defines the raw materials, quantities, and operations required to manufacture one unit of a finished item.",
        "A Work Order is created from a BOM and tracks the manufacturing of a specific quantity of an item, including material and operation status.",
        "Job Cards track the execution of individual operations within a Work Order, including time logs and operator assignment.",
        "A Production Plan aggregates demand from Sales Orders or forecasts to determine what needs to be manufactured and by when.",
        "Routing defines the sequence of operations (and the workstations they run on) that a BOM's manufacturing process follows.",
        "Subcontracted manufacturing sends a BOM's raw materials to an external supplier who returns the finished semi-assembly or product.",
        "Workstations represent machines or work centers and can track hourly operating cost, capacity, and downtime.",
        "Multi-level BOMs reference other BOMs as sub-assemblies, allowing complex products to be broken into manageable manufacturing stages.",
        "Backflushing automatically consumes raw materials from stock based on the BOM when a Work Order's manufacture is completed, without manual stock entries.",
        "The BOM Comparison tool highlights cost or component differences between two versions of a BOM for the same item.",
    ],
    "hr": [
        "A Leave Application is submitted by an employee against a Leave Type and is approved by their reporting manager before leave is deducted.",
        "Attendance can be marked manually, via biometric device integration, or through a check-in/check-out mobile app.",
        "A Salary Slip is generated per employee per payroll period based on their assigned Salary Structure, including earnings and deductions.",
        "A Payroll Structure defines the components (basic pay, allowances, deductions) that make up an employee's salary.",
        "The Holiday List defines company or location-specific non-working days, which affect attendance and leave calculations.",
        "Employee Onboarding uses a checklist-driven process to track document collection, asset assignment, and orientation tasks for new hires.",
        "Appraisal Cycles collect structured performance feedback from managers and peers over a defined review period.",
        "Expense Claims let employees submit reimbursable expenses, which route through an approval workflow before being paid out.",
        "Shift Types define working hours, and employees can be assigned rotating or fixed shifts that affect attendance calculation.",
        "Employee Separation tracks the offboarding process, including asset return, full and final settlement, and exit interview steps.",
    ],
    "projects": [
        "A Project groups related Tasks, Timesheets, and expenses, and can track overall budget, billing, and profitability.",
        "Tasks within a project can have dependencies, assignees, priority, and expected start/end dates, visualized in a Gantt chart.",
        "Timesheets log hours worked against specific tasks or projects and are the basis for billing time-and-materials clients.",
        "Project billing can be time-based (from timesheets), milestone-based, or a fixed cost, depending on the project type.",
        "Project Templates let recurring project structures (task lists, standard timelines) be reused for similar new projects.",
        "Billable vs non-billable hours are distinguished in timesheets to separate client-chargeable work from internal effort.",
        "Linking a Sales Order to a Project ties revenue recognition and delivery obligations to the project's actual execution.",
        "Project cost estimates compare planned budget against actual expenses and timesheet costs as the project progresses.",
        "Resource allocation reports show how team members' time is distributed across multiple concurrent projects.",
        "A Project's status (Open, Completed, Cancelled) controls whether new tasks and timesheets can still be logged against it.",
    ],
    "assets": [
        "An Asset record tracks a purchased fixed asset's cost, location, custodian, and depreciation details from acquisition to disposal.",
        "Depreciation Schedules are generated automatically based on the asset's cost, useful life, and chosen depreciation method.",
        "Straight Line depreciation spreads cost evenly over the asset's useful life; Written Down Value applies a fixed percentage to the remaining value each period.",
        "Asset Movement records track relocation of an asset between departments, employees, or physical locations.",
        "Asset Maintenance schedules preventive or breakdown maintenance tasks and logs completed maintenance history.",
        "Disposing of an asset (sale, scrap, or loss) is recorded via an Asset Disposal action, which posts the appropriate accounting entries.",
        "Asset capitalization converts a Work In Progress (CWIP) asset into a fully capitalized, depreciating asset once it's ready for use.",
        "Asset Value Adjustments record impairments or revaluations that change an asset's book value outside the normal depreciation schedule.",
        "Low Value Asset write-off policies let assets below a configured cost threshold be expensed immediately instead of depreciated.",
        "Asset custodian assignment tracks which employee is currently responsible for a given asset at any point in time.",
    ],
    "quality": [
        "A Quality Inspection records pass/fail results against defined parameters for incoming purchases, in-process manufacturing, or outgoing deliveries.",
        "Quality Inspection Templates define the parameters, acceptance criteria, and sample size used for a given item or process.",
        "A Non-Conformance Report documents a quality failure, its root cause, and the corrective action taken to prevent recurrence.",
        "Quality Goals set measurable targets (e.g. defect rate, on-time delivery) with a target date, tracked over time against actuals.",
        "Quality Procedures document standardized step-by-step processes used to maintain consistent quality across operations.",
        "Incoming Quality Inspection is linked to a Purchase Receipt, blocking stock from being used until it passes inspection.",
        "In-process Quality Inspection is linked to manufacturing operations to catch defects before a product reaches final assembly.",
        "Outgoing Quality Inspection is linked to a Delivery Note to ensure only inspected, passing stock is shipped to customers.",
        "Quality Review meetings and Quality Feedback records provide a structured way to track continuous improvement initiatives.",
        "Quality Actions link corrective and preventive actions directly to the non-conformance reports that triggered them.",
    ],
    "crm": [
        "A Lead represents an unqualified prospect and is the entry point into the CRM pipeline before any real sales conversation has occurred.",
        "Converting a Lead to an Opportunity marks it as a qualified prospect actively being pursued for a specific deal.",
        "Opportunities track probability of closing, expected deal value, and expected closing date through defined sales stages.",
        "Lead Sources (website, referral, campaign, cold call) are tracked to measure which channels generate the most qualified pipeline.",
        "Communication logs (calls, emails) attached to a Lead or Opportunity give the full history of interactions with a prospect.",
        "Lost Opportunities are marked with a lost reason, which feeds into reporting on why deals fail to close.",
        "Territory-based lead assignment automatically routes new leads to the right sales person based on region rules.",
        "Campaigns group marketing activities and let leads generated from a specific campaign be tracked back to that source.",
        "Converting an Opportunity into a Quotation moves a qualified deal from CRM into the formal Selling workflow.",
        "The Sales Funnel report visualizes how many leads and opportunities exist at each pipeline stage, highlighting where deals stall.",
    ],
    "support": [
        "An HD Ticket is the core record for a support request, tracking status, priority, assigned agent, and full communication history.",
        "SLA (Service Level Agreement) policies define response and resolution time targets based on ticket priority or customer type.",
        "Canned Responses let support agents insert pre-written replies for common questions to speed up response time.",
        "Knowledge Base articles let customers self-serve answers to common questions before or instead of raising a ticket.",
        "Ticket escalation rules automatically reassign or flag tickets that breach their SLA response or resolution time.",
        "A 'permission error' in Frappe usually means the user's Role doesn't have the required permission level on that DocType -- check Role Permissions Manager.",
        "A 'duplicate entry' error typically means a unique field (like a naming series value) collided -- check for an existing record with the same ID.",
        "Clearing the cache (bench clear-cache) resolves many stale-data issues after code or config changes.",
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
