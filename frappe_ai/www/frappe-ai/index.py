import frappe

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw("Please log in to use Frappe AI.", frappe.PermissionError)

    context.csrf_token = frappe.sessions.get_csrf_token()
    context.user = frappe.session.user
