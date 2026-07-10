"""
Seeds sample AI Agent Document records for the 10 default ERPNext agents,
matching the exact doctype breakdown: Internal (General), Accounts,
Buying, Selling, CRM, HR, Manufacturing, Project, Inventory, Support.

Dict keys here MUST match the actual AI Agent document `name` (Title
Case, e.g. "Project" not "Projects", "Inventory" not "Stock") -- these
are Frappe document names, not just internal labels, since AI Agent's
autoname is overridden by the explicit "name" field in the AI Agent
fixture.

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
        # Company & Multi-Company
        "A Company is the top-level master in ERPNext. All transactions — invoices, stock entries, journal entries — are scoped to a specific Company.",
        "Multiple Companies can be created on one ERPNext site. Each Company has fully separate Chart of Accounts, warehouses, and reports.",
        "To set up a new Company in ERPNext, go to Accounting > Company > New Company. You must provide a Company Name, default currency, and country.",
        "Inter-Company Transactions in ERPNext allow one Company to raise a Sales Invoice against another Company on the same site, with automatic mirroring.",
        # Item & Item Group
        "An Item is the master record for any product or service bought, sold, or stocked in ERPNext. It defines UOM, Item Group, valuation method, and default warehouse.",
        "Item Groups form a tree hierarchy used for reporting, pricing rules, and default account/warehouse settings. An Item must belong to exactly one Item Group.",
        "Item Variants allow one Template Item to generate multiple SKUs based on Item Attributes such as size or color, without duplicating master data.",
        "To create an Item in ERPNext: Stock > Items and Pricing > Item > New. Set Item Code, Item Name, Item Group, and UOM at minimum.",
        "The 'Maintain Stock' checkbox on an Item controls whether ERPNext tracks inventory for it. Uncheck it for service items.",
        # Warehouse
        "A Warehouse in ERPNext represents a physical or virtual stock location. Every stock transaction must reference a source and/or target Warehouse.",
        "Warehouses can be arranged in a parent-child hierarchy in ERPNext for grouped reporting. A child warehouse rolls up into its parent in Stock Balance reports.",
        # Address & Contact
        "An Address record in ERPNext can be linked to a Customer, Supplier, Company, or Contact. One party can have multiple addresses with different address types.",
        "A Contact record stores a person's phone, email, and designation. It can be linked to one or more Customers, Suppliers, or Leads.",
        # Email Account
        "Email Accounts in ERPNext configure outgoing SMTP and incoming IMAP/POP3 servers. Linked Email Accounts can auto-create Communications or HD Tickets on incoming mail.",
        # Naming Series
        "Naming Series in ERPNext define the auto-generated ID format for documents (e.g. INV-.YYYY.-.####). Configure them under Settings > Naming Series.",
        # Custom Fields
        "Custom Fields can be added to any DocType in ERPNext via Customization > Custom Field, without modifying core code. They persist across upgrades.",
        # DocType
        "A DocType is the core building block of the Frappe Framework. It defines a database table, form layout, validations, and permissions for any record type in ERPNext.",
        # Fiscal Year
        "A Fiscal Year in ERPNext defines the accounting period for a Company. It affects reports, budgets, and tax filings. One Fiscal Year is set as the default per Company.",
        # Currency
        "Currency records in ERPNext define the exchange rate and formatting for each currency used in transactions and multi-currency accounting.",
        # User & Role
        "Users in ERPNext are assigned Roles. Roles control which DocTypes a user can read, write, create, delete, submit, or cancel.",
        "The Role Permissions Manager in ERPNext (Setup > Role Permissions Manager) lets administrators configure field-level and document-level permissions per Role.",
    ],

    "Accounts": [
        # Chart of Accounts
        "The Chart of Accounts (COA) in ERPNext defines the tree of ledger accounts — Assets, Liabilities, Income, Expense, Equity — used across all transactions. Each Company has its own COA.",
        "To create a new ledger account in ERPNext: Accounting > Chart of Accounts > Add Child. Set Account Name, Account Type, and parent account.",
        "Account Types in ERPNext (Receivable, Payable, Bank, Cash, Tax, etc.) control how the account appears in financial reports and which transactions can post to it.",
        # Journal Entry
        "A Journal Entry (JE) in ERPNext is used to post manual accounting transactions: adjustments, provisions, opening balances, and corrections between ledger accounts.",
        "To post a Journal Entry in ERPNext: Accounting > Journal Entry > New. Add debit and credit rows ensuring total debit equals total credit before submitting.",
        # Payment Entry
        "A Payment Entry in ERPNext records money received from a customer or paid to a supplier. It can be reconciled against one or more outstanding Sales or Purchase Invoices.",
        "To create a Payment Entry from a Sales Invoice in ERPNext: open the submitted invoice and click 'Create > Payment'. The amount and party are pre-filled.",
        # Sales & Purchase Invoice
        "A Sales Invoice in ERPNext bills a customer for goods or services delivered. Submitting it posts a debit to the Receivable account and a credit to the Income account.",
        "A Purchase Invoice in ERPNext records a supplier's bill. Submitting it posts a credit to the Payable account and a debit to the relevant Expense or Asset account.",
        "To create a Sales Invoice from a Sales Order in ERPNext: open the submitted Sales Order and click 'Create > Sales Invoice'. Delivered quantities are pre-filled.",
        # Asset & Depreciation
        "An Asset record in ERPNext tracks a fixed asset's purchase cost, location, and depreciation schedule. Asset Depreciation Entries reduce its book value each period.",
        "ERPNext supports two Asset depreciation methods: Straight Line Method (equal amounts each period) and Written Down Value (fixed percentage of remaining book value).",
        "To create an Asset in ERPNext: Accounting > Assets > Asset > New. Set Item, Purchase Date, Gross Purchase Amount, Depreciation Method, and useful life.",
        # Cost Center
        "Cost Centers in ERPNext allow tracking income and expense by department, project, or branch, independent of the Chart of Accounts. Every P&L transaction references a Cost Center.",
        # Reports
        "The General Ledger report in ERPNext (Accounting > Reports > General Ledger) shows every posted transaction for every account — the primary audit tool.",
        "The Profit & Loss Statement in ERPNext summarizes income and expense accounts over a selected period to show net profit or loss.",
        "The Balance Sheet in ERPNext shows Assets, Liabilities, and Equity as of a specific date. It must always balance: Assets = Liabilities + Equity.",
        "The Accounts Receivable report in ERPNext shows outstanding customer invoices aged by due date. Use it to follow up on overdue payments.",
        "The Accounts Payable report in ERPNext shows outstanding supplier invoices aged by due date. Use it to manage cash outflow and avoid late penalties.",
        # Tax
        "Tax Templates in ERPNext (Sales Taxes and Charges Template, Purchase Taxes and Charges Template) define tax rows that auto-populate on transactions.",
        "GST configuration in ERPNext India requires setting up Tax Categories, GST HSN Codes on Items, and GSTIN on Company and Customer/Supplier records.",
        # Bank Reconciliation
        "Bank Reconciliation in ERPNext matches Payment Entries and Journal Entries against your bank statement to identify uncleared transactions.",
    ],

    "Buying": [
        # Supplier
        "A Supplier record in ERPNext stores vendor details, payment terms, default currency, and tax information used across all purchase transactions.",
        "To create a Supplier in ERPNext: Buying > Supplier > New. Set Supplier Name, Supplier Group, and default currency at minimum.",
        # Material Request
        "A Material Request (MR) in ERPNext is the standard trigger for procurement. It can be raised manually or auto-generated when stock falls below the reorder level.",
        "Material Request types in ERPNext: Purchase (triggers procurement), Material Transfer (internal movement), Material Issue (consumption), and Manufacture (production).",
        "To raise a Material Request in ERPNext: Stock > Material Request > New. Add items, required quantities, and required by date, then submit.",
        # RFQ
        "A Request for Quotation (RFQ) in ERPNext is sent to multiple suppliers to gather pricing before deciding on a Purchase Order.",
        "To create an RFQ from a Material Request in ERPNext: open the submitted MR and click 'Create > Request for Quotation'. Suppliers are added manually.",
        # Supplier Quotation
        "A Supplier Quotation in ERPNext records a supplier's response to an RFQ. Multiple Supplier Quotations can be compared side-by-side using the Supplier Quotation Comparison tool.",
        # Purchase Order
        "A Purchase Order (PO) in ERPNext confirms quantities, rates, and delivery dates with a supplier. It is created from an approved MR or Supplier Quotation.",
        "To create a Purchase Order from a Supplier Quotation in ERPNext: open the Supplier Quotation and click 'Create > Purchase Order'.",
        "Purchase Order approval in ERPNext can require manager sign-off above a configured amount using the Workflow feature before the PO is submitted to the supplier.",
        # Purchase Receipt
        "A Purchase Receipt (PR) in ERPNext records goods physically received from a supplier. Submitting it updates stock quantities in the selected warehouse.",
        "To create a Purchase Receipt from a Purchase Order in ERPNext: open the submitted PO and click 'Create > Purchase Receipt'. Received quantities are entered here.",
        # Purchase Invoice
        "A Purchase Invoice in ERPNext is created from a Purchase Receipt and records the supplier's bill. It posts accounting entries and creates the payable.",
        # Landed Cost
        "A Landed Cost Voucher in ERPNext allocates additional costs (freight, customs, insurance) across received items on a Purchase Receipt for accurate stock valuation.",
        # Blanket PO
        "A Blanket Purchase Order in ERPNext sets an agreed quantity and rate with a supplier over a period. Individual Purchase Orders are released against it as needed.",
        # Reports
        "The Purchase Analytics report in ERPNext (Buying > Reports) breaks down spend by supplier, item, or item group over a selected date range.",
        "The Purchase Order Trends report in ERPNext shows pending, received, and billed quantities across Purchase Orders over a period.",
    ],

    "Selling": [
        # Customer
        "A Customer record in ERPNext stores billing details, credit limit, default price list, and default currency used across all sales transactions.",
        "To create a Customer in ERPNext: Selling > Customer > New. Set Customer Name, Customer Group, and Territory at minimum.",
        # Quotation
        "A Quotation in ERPNext is a non-binding offer sent to a prospective or existing customer. It can be converted into a Sales Order once the customer accepts.",
        "To create a Quotation in ERPNext: Selling > Quotation > New. Set the customer (or lead), add items with rates, and submit.",
        # Sales Order
        "A Sales Order (SO) in ERPNext confirms a customer's order: items, quantities, rates, and delivery date. It is the basis for delivery and invoicing.",
        "To create a Sales Order from a Quotation in ERPNext: open the submitted Quotation and click 'Create > Sales Order'.",
        # Pick List
        "A Pick List in ERPNext consolidates items needed to fulfill one or more Sales Orders into a single warehouse picking task before packaging and shipping.",
        # Delivery Note
        "A Delivery Note (DN) in ERPNext records goods physically shipped to a customer. Submitting it reduces stock from the source warehouse.",
        "To create a Delivery Note from a Sales Order in ERPNext: open the submitted SO and click 'Create > Delivery Note'.",
        # Sales Invoice
        "A Sales Invoice in ERPNext is created from a Delivery Note or Sales Order and bills the customer. Submitting it creates the receivable and posts income.",
        # Pricing Rules
        "Pricing Rules in ERPNext apply automatic discounts or price overrides based on customer, customer group, item, item group, quantity threshold, or date range.",
        "To create a Pricing Rule in ERPNext: Accounts > Pricing Rule > New. Set Apply On (Item/Item Group), condition, discount type, and applicable party.",
        # Credit Limit
        "Customer credit limits in ERPNext block new Sales Orders or Invoices once the customer's outstanding receivable balance crosses the configured threshold.",
        # Sales Return
        "A Sales Return in ERPNext is processed as a Sales Invoice with 'Is Return' checked, referencing the original invoice to reverse stock and accounting entries.",
        # Territory & Customer Group
        "Territory in ERPNext organizes customers by region for sales reporting and lead assignment. Customer Group organizes customers by type (e.g. Commercial, Retail).",
        # Reports
        "The Sales Analytics report in ERPNext shows revenue by customer, item, territory, or sales person over a selected date range.",
        "The Sales Order Trends report in ERPNext shows pending, delivered, and billed quantities across Sales Orders over a period.",
    ],

    "CRM": [
        # Lead
        "A Lead in ERPNext (or Frappe CRM) represents an unqualified prospect. It captures contact info and source of interest before any real sales conversation.",
        "To create a Lead in ERPNext: CRM > Lead > New. Set Lead Name, company name, email, phone, and Lead Source.",
        "Lead Sources in ERPNext (website, referral, campaign, cold call) are tracked on Leads and Opportunities to measure which channels produce the most pipeline.",
        # Opportunity / Deal
        "An Opportunity in ERPNext (called a Deal in Frappe CRM) tracks a qualified prospect through sales pipeline stages with probability of closing and expected value.",
        "To convert a Lead to an Opportunity in ERPNext: open the Lead and click 'Create > Opportunity'. Customer and contact details are carried over.",
        "Opportunity stages in ERPNext can be customized in CRM > Setup > Opportunity Stage. Each stage represents a step in your sales process.",
        # Frappe CRM specific
        "Frappe CRM is a standalone CRM application built on the Frappe Framework. It uses 'Leads' and 'Deals' instead of ERPNext's 'Leads' and 'Opportunities'.",
        "The Frappe CRM Connector app links Frappe CRM Deals to ERPNext, enabling one-click Quotation creation directly from a Deal without switching applications.",
        "In Frappe CRM, a Deal has a kanban pipeline view showing all deals across stages. Drag a card to move the deal to the next stage.",
        # Quotation from CRM
        "A Quotation in ERPNext can be generated directly from an Opportunity once pricing terms are discussed, moving the prospect toward a formal Sales Order.",
        # Communication
        "Communication logs in ERPNext (calls, emails, WhatsApp messages) attached to a Lead or Opportunity give the full interaction history with a prospect.",
        # Lost
        "Lost Opportunities in ERPNext are marked with a lost reason (e.g. Price, Competitor, No Budget). This feeds into the Lost Reasons report for pipeline analysis.",
        # Territory assignment
        "Territory-based lead assignment in ERPNext automatically routes new leads to the right sales person based on region rules configured in the Territory doctype.",
        # Reports
        "The CRM Pipeline report (Sales Funnel) in ERPNext shows how many leads and opportunities exist at each stage, highlighting where prospects stall or drop off.",
        "The Lead Source report in ERPNext shows which lead sources (website, referral, campaign) generate the most leads and conversions.",
    ],

    "HR": [
        # Employee
        "An Employee record in ERPNext is the master data for a staff member, linking to their attendance, leave, payroll, and appraisal records.",
        "To create an Employee in ERPNext: Human Resources > Employee > New. Set Employee Name, Company, Department, Date of Joining, and reporting manager.",
        # Leave
        "A Leave Application in ERPNext is submitted by an employee against a Leave Type and approved by their reporting manager before leave is deducted from their balance.",
        "Leave Allocation in ERPNext assigns a number of leave days to an employee for a Leave Type over a period (e.g. 18 days Annual Leave for FY 2025).",
        "Leave Types in ERPNext (Annual, Sick, Casual, Maternity) define whether leave is paid, whether unused leave can be carried forward, and encashment rules.",
        # Salary
        "A Salary Structure in ERPNext defines the earning and deduction components (Basic Pay, HRA, PF, Tax) that make up a role's compensation.",
        "A Salary Structure Assignment links a specific Employee to a Salary Structure with an effective-from date. Pay changes are versioned over time.",
        "A Salary Slip in ERPNext is generated per employee per payroll period based on their active Salary Structure Assignment. It calculates actual amounts from formula components.",
        "To run payroll in ERPNext: HR > Payroll > Process Payroll. Select Company, Payroll Frequency, and period, then Generate Salary Slips, verify, and Submit.",
        # Attendance
        "Attendance records in ERPNext mark an employee as Present, Absent, Half Day, or On Leave for each working day. They feed into salary slip calculations.",
        "The Auto Attendance feature in ERPNext can mark attendance from biometric device check-in logs imported into the Employee Checkin doctype.",
        # Shift
        "A Shift Type in ERPNext defines working hours, grace period for late check-in, and early exit tolerance for a category of work schedule.",
        "A Shift Assignment links a specific Employee to a Shift Type over a date range, supporting fixed or rotating shift patterns.",
        # Holiday
        "The Holiday List in ERPNext defines company or location-specific non-working days. It is assigned to Employees or Companies and affects attendance and leave calculations.",
        # Appraisal
        "Appraisal Cycles in ERPNext collect structured performance feedback from managers and peers over a defined review period using configurable KRAs and ratings.",
        # Onboarding
        "Employee Onboarding in ERPNext uses a checklist-driven process to track document collection, asset assignment, and orientation tasks for new hires.",
        # Reports
        "The Monthly Attendance Sheet report in ERPNext shows daily attendance status for all employees in a department for a selected month.",
        "The Salary Register report in ERPNext shows a summary of all Salary Slips for a payroll period across all employees.",
    ],

    "Manufacturing": [
        # BOM
        "A Bill of Materials (BOM) in ERPNext defines the raw materials, quantities, scrap percentage, and Operations required to manufacture one unit of a finished Item.",
        "To create a BOM in ERPNext: Manufacturing > BOM > New. Set the finished Item, add raw material rows with quantities and UOM, add Operations if routing is used, then submit.",
        "Multi-level BOMs in ERPNext reference sub-assembly BOMs as components, allowing complex products to be broken into manageable manufacturing stages.",
        "The BOM Comparison Tool in ERPNext lets you compare two BOMs side-by-side to identify differences in materials, quantities, or operations.",
        # Work Order
        "A Work Order (WO) in ERPNext is created from a BOM and tracks the manufacturing of a specific quantity of a finished item, including material and operation status.",
        "To create a Work Order in ERPNext: Manufacturing > Work Order > New. Select the BOM, set quantity, planned start date, and target warehouse, then submit.",
        "Work Order status in ERPNext moves through: Draft > Submitted > In Process > Completed. Stock Entries are made against the WO to move it forward.",
        # Job Card
        "Job Cards in ERPNext track the execution of individual Operations within a Work Order. Operators log start/end times and the Job Card records actual time taken.",
        # Stock Entries for Manufacturing
        "Stock Entry type 'Material Transfer for Manufacturing' in ERPNext moves raw materials from a source warehouse to the Work-in-Progress (WIP) warehouse before production starts.",
        "Stock Entry type 'Manufacture' in ERPNext records the consumption of raw materials from the WIP warehouse and the receipt of the finished item into the target warehouse.",
        # Production Plan
        "A Production Plan in ERPNext aggregates demand from open Sales Orders or material forecasts to determine what needs to be manufactured and by when.",
        "To create a Production Plan in ERPNext: Manufacturing > Production Plan > New. Get Items from Sales Orders or Material Requests, plan sub-assemblies, then create Work Orders.",
        # Routing & Operation
        "Routing in ERPNext defines the sequence of Operations (and the workstations they run on) that a BOM's manufacturing process follows.",
        "An Operation in ERPNext defines a single manufacturing step (e.g. Cutting, Assembly, Painting, Quality Check) with a standard time for costing.",
        # Backflushing
        "Backflushing in ERPNext automatically consumes raw materials based on the BOM quantities when a Work Order's Manufacture Stock Entry is created, without listing each material manually.",
        # Reports
        "The Production Planning Report in ERPNext shows Work Orders with planned vs actual start/end dates and completion percentages.",
        "The BOM Stock Report in ERPNext shows the current stock availability of all raw materials required for a selected BOM and quantity.",
    ],

    "Project": [
        # Project
        "A Project in ERPNext is the top-level record for tracking a body of work. It has a status, expected start/end dates, and a percentage completion field.",
        "To create a Project in ERPNext: Projects > Project > New. Set Project Name, status, expected dates, and optionally link it to a Customer for billing.",
        # Task
        "A Task in ERPNext is a unit of work linked to a Project. It has assignees, priority, expected start/end dates, and dependencies on other Tasks.",
        "To create a Task in ERPNext: Projects > Task > New (or from the Task section inside a Project). Set subject, project, assigned to, and expected dates.",
        "Task dependencies in ERPNext let one Task be blocked by another (Dependent On). The Gantt chart view in the Project visualizes these dependencies.",
        "Task status in ERPNext: Open, Working, Pending Review, Completed, Cancelled. Status drives how work is tracked and surfaced in project views.",
        # Timesheet
        "A Timesheet in ERPNext logs hours worked against specific Tasks by an employee. It is the basis for billing time-and-materials clients and tracking effort.",
        "To create a Timesheet in ERPNext: Projects > Timesheet > New. Add rows with Task, From Time, To Time, and whether the hours are billable.",
        "Billable vs non-billable hours are distinguished on a Timesheet row in ERPNext to separate client-chargeable work from internal overhead.",
        "A Timesheet in ERPNext must be submitted before its hours are considered final for billing or reporting purposes.",
        # Billing from Timesheet
        "A Sales Invoice can be generated directly from approved Timesheet entries in ERPNext for time-and-materials billing: open the Timesheet and click 'Create > Sales Invoice'.",
        # Project Templates
        "Project Templates in ERPNext define a standard set of Tasks and their dependencies that can be applied when a new Project of that type is created.",
        # Reports
        "The Project Summary report in ERPNext shows overall completion, total hours logged, and billing status across all active projects.",
        "The Daily Timesheet Summary report in ERPNext shows hours logged per employee per day for a selected date range.",
        "The Delayed Tasks report in ERPNext lists Tasks whose expected end date has passed but whose status is not yet Completed.",
    ],

    "Inventory": [
        # Stock Entry
        "A Stock Entry in ERPNext records any material movement — transfer, receipt, issue, or manufacturing consumption — and updates the Stock Ledger in real time.",
        "Stock Entry types in ERPNext: Material Receipt, Material Issue, Material Transfer, Material Transfer for Manufacturing, Manufacture, Repack, Send to Subcontractor.",
        "To create a Stock Entry in ERPNext: Stock > Stock Entry > New. Select the Stock Entry Type, add items with quantities and warehouses, then submit.",
        # Stock Balance
        "The Stock Balance report in ERPNext (Stock > Reports > Stock Balance) shows current on-hand quantity and valuation for every item across every warehouse as of a selected date.",
        # Stock Ledger
        "The Stock Ledger report in ERPNext is the definitive transaction-level record of every stock movement for an item across all warehouses, including valuation rate changes.",
        # Stock Reconciliation
        "Stock Reconciliation in ERPNext adjusts system quantities to match a physical count. It is the standard tool for correcting inventory discrepancies after a physical stock-take.",
        "To do a Stock Reconciliation in ERPNext: Stock > Stock Reconciliation > New. Upload or enter actual counts per item per warehouse, then submit to adjust quantities and value.",
        # Batch & Serial No
        "Batch tracking in ERPNext groups stock by manufacturing batch (useful for expiry date management). Enable it on the Item with 'Has Batch No' checkbox.",
        "Serial Number tracking in ERPNext tracks individual units of an item uniquely. Enable it on the Item with 'Has Serial No' checkbox.",
        "To receive serialized items in ERPNext via a Purchase Receipt, enter one Serial Number per unit in the Serial No field on the item row.",
        # Reorder
        "Reorder levels in ERPNext, set per Item per Warehouse, can automatically trigger a Material Request when on-hand stock falls below the defined level.",
        "The Reorder Point Planning report in ERPNext shows items currently below their reorder level across warehouses.",
        # Valuation
        "ERPNext supports two stock valuation methods: FIFO (First In First Out) and Moving Average. The method is set on the Item and affects cost of goods sold calculation.",
        "Moving Average valuation in ERPNext recalculates the average cost of an item every time new stock is received, blending old and new costs.",
        # Putaway
        "Putaway Rules in ERPNext automatically assign a target warehouse or warehouse location to inbound stock based on Item or Item Group rules.",
        # Reports
        "The Itemwise Recommended Reorder Level report in ERPNext suggests reorder levels based on consumption rate and lead time.",
        "The Stock Ageing report in ERPNext shows how long current stock has been sitting in each warehouse, helping identify slow-moving inventory.",
    ],

    "Support": [
        # HD Ticket
        "An HD Ticket (Helpdesk Ticket) in Frappe Helpdesk is the core support record. It tracks status, priority, assigned agent, SLA, and the full communication history.",
        "HD Ticket statuses in Frappe Helpdesk: Open, Replied, Resolved, Closed. SLA timers run while the ticket is Open.",
        "To create an HD Ticket in Frappe Helpdesk: Helpdesk > New Ticket. Set Customer, Subject, and Description. The ticket is assigned to an agent based on assignment rules.",
        # SLA
        "An SLA (Service Level Agreement) in Frappe Helpdesk defines response time and resolution time targets based on ticket priority (Low, Medium, High, Urgent) or customer tier.",
        "SLA breach in Frappe Helpdesk triggers an automatic escalation — the ticket is flagged and optionally re-assigned to a senior agent or manager.",
        # Canned Responses
        "Canned Responses in Frappe Helpdesk are pre-written reply templates agents can insert into ticket replies for common questions, saving time on repetitive responses.",
        # Knowledge Base
        "Knowledge Base articles in Frappe Helpdesk allow customers to self-serve answers to common questions before raising a ticket. Articles are organized by category.",
        # Frappe errors
        "A 'Permission Error' in ERPNext means the logged-in user's Role does not have the required permission level on that DocType. Fix it via Setup > Role Permissions Manager.",
        "A 'Duplicate Entry' error in ERPNext typically means a unique field (like a naming series value or unique constraint) collided with an existing record.",
        "Running 'bench clear-cache' on the Frappe server resolves many stale-data issues after code changes, DocType changes, or configuration updates.",
        "Background jobs in ERPNext can be monitored under 'Background Jobs' in the Desk (top right menu). Pending or failed jobs can be seen via bench --site <site> show-pending-jobs.",
        "A failed 'bench migrate' should be diagnosed by reading the bench error log (logs/worker.error.log) before retrying, since re-running blind can hide the root cause.",
        "If a Frappe/ERPNext form is not saving, check the browser console for JavaScript errors and the server error log for Python tracebacks.",
        "To reset a forgotten ERPNext Administrator password: bench --site <site> set-admin-password <new-password> from the server CLI.",
        "If ERPNext emails are not sending, check the Email Account configuration (outgoing SMTP settings) and the Email Queue under Settings > Email Queue for error messages.",
        "The Frappe error log is accessible from the Desk under Settings > Error Log. Each entry shows the traceback, user, and timestamp of the error.",
        # Bench commands
        "bench restart restarts all Frappe processes (web server, workers, scheduler). Run it after code changes or config updates on a production server.",
        "bench update fetches the latest code from git, runs patches, builds assets, and restarts the server. Use bench update --pull --patch --build on production.",
    ],
}


def run():
    created = 0
    for agent_name, docs in SAMPLE_DOCS.items():
        if not frappe.db.exists("AI Agent", agent_name):
            print(f"Skipping '{agent_name}' -- no AI Agent record with that name exists.")
            continue
        for content in docs:
            frappe.get_doc(
                {"doctype": "AI Agent Document", "agent": agent_name, "content": content}
            ).insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    print(f"Seeded {created} sample knowledge base documents across {len(SAMPLE_DOCS)} agents.")
