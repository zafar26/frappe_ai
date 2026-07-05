"""
Seeds sample AI Agent Document records for the three default agents.

AI Agent Document isn't shipped as a fixture (unlike AI Agent and Router
Training Example) because inserting it triggers embedding into ChromaDB,
which needs the embedding model available -- better to run explicitly
after the app + its Python dependencies are fully installed.

Run once after `bench install-app ai_dispatch` and `bench migrate`:
    bench --site <site> execute ai_dispatch.setup.seed_sample_data.run
"""

import frappe

SAMPLE_DOCS = {
    "tech_support": [
        "To reset your password, go to the login page and click 'Forgot Password', then follow the link sent to your registered email.",
        "If the app crashes on startup, try clearing the app cache from Settings > Storage, then restart your device.",
        "For a 404 error, check that the URL is typed correctly and that the page hasn't been moved or deleted.",
        "Software updates can be installed from Settings > System > Software Update. A restart is required after installing.",
        "If your internet keeps dropping, restart your router, check for firmware updates, and contact your ISP if the issue persists.",
        "To connect to the company VPN, install the VPN client from the internal portal and log in with your employee credentials.",
        "Two factor authentication can be enabled in Account Settings > Security > Two-Factor Authentication.",
        "If the system is running slow, check for background processes consuming CPU, and ensure at least 15% of disk space is free.",
        "Deleted files can often be recovered from the Recycle Bin or Trash within 30 days of deletion.",
        "Server downtime notices are posted on the status page with estimated restoration times.",
    ],
    "hr": [
        "Full-time employees accrue 1.5 vacation days per month, up to a maximum of 18 days per year.",
        "Payroll is processed on the last working day of each month; payslips are available online by the 1st.",
        "Parental leave requests should be submitted at least 30 days in advance through the HR portal.",
        "The company supports remote work up to 3 days per week, subject to manager approval.",
        "To update your bank details for salary deposits, submit a request through the Employee Self-Service portal.",
        "Workplace complaints, including harassment concerns, can be reported confidentially to HR or the ethics hotline.",
        "Sick leave of up to 2 days does not require a doctor's note; longer absences require medical certification.",
        "The standard notice period for resignation is 30 days for permanent employees.",
        "Performance appraisals are conducted twice a year, in June and December.",
        "Employee referral bonuses are paid out after the referred candidate completes 90 days of employment.",
    ],
    "sales": [
        "The Starter plan costs $19/month and includes up to 5 users and basic reporting.",
        "The Pro plan costs $49/month and includes up to 20 users, advanced analytics, and priority support.",
        "The Enterprise plan is custom-priced and includes unlimited users, dedicated account management, and SLA guarantees.",
        "All plans include a 14-day free trial with no credit card required.",
        "Annual billing gives a 20% discount compared to monthly billing on all plans.",
        "We accept payment via credit card, ACH bank transfer, and wire transfer for annual enterprise contracts.",
        "Refunds are available within 30 days of purchase if you're not satisfied, no questions asked.",
        "Educational institutions receive a 40% discount on Pro and Enterprise plans with valid accreditation.",
        "Reseller partners receive tiered volume discounts starting at 10 licenses.",
        "Existing customers can upgrade or downgrade their plan anytime from Account > Billing.",
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
    print(f"Seeded {created} sample knowledge base documents.")
