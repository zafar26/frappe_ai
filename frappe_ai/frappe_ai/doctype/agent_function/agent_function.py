import json

import frappe
from frappe.model.document import Document


class AgentFunction(Document):
    def validate(self):
        self._validate_parameters_json()
        self._validate_dispatch_handler()

    def _validate_parameters_json(self):
        try:
            parsed = json.loads(self.parameters or "{}")
        except (json.JSONDecodeError, TypeError) as e:
            frappe.throw(f"Parameters must be valid JSON: {e}")

        if not isinstance(parsed, dict):
            frappe.throw("Parameters must be a JSON object, e.g. {\"customer\": \"string (required)\"}.")

    def _validate_dispatch_handler(self):
        try:
            handler = frappe.get_attr(self.dispatch_handler)
        except Exception as e:
            frappe.throw(
                f"Dispatch Handler '{self.dispatch_handler}' could not be imported: {e}. "
                "It must be a dotted path to an existing Python function, e.g. "
                "frappe_ai.frappe_ai.page.agent_caller.agent_caller.create_sales_order."
            )
        if not callable(handler):
            frappe.throw(f"Dispatch Handler '{self.dispatch_handler}' is not callable.")

    def on_update(self):
        # Function list is cached in-process (see agent_caller._get_functions) for
        # speed; invalidate it whenever a function is created/edited so changes
        # take effect immediately without a restart.
        frappe.cache().delete_value("frappe_ai:agent_functions")

    def on_trash(self):
        frappe.cache().delete_value("frappe_ai:agent_functions")
