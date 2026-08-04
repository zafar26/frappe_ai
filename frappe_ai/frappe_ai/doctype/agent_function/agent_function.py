import json

import frappe
from frappe.model.document import Document


class AgentFunction(Document):
    def validate(self):
        self._validate_parameters_json()
        self._validate_script_compiles()

    def _validate_parameters_json(self):
        try:
            parsed = json.loads(self.parameters or "{}")
        except (json.JSONDecodeError, TypeError) as e:
            frappe.throw(f"Parameters must be valid JSON: {e}")

        if not isinstance(parsed, dict):
            frappe.throw("Parameters must be a JSON object, e.g. {\"customer\": \"string (required)\"}.")

    def _validate_script_compiles(self):
        # We only check the script is syntactically valid Python here -- we
        # can't safely *run* it at save time, since we don't have real
        # arguments (`args`) yet. Runtime errors (e.g. args["foo"] missing)
        # still surface the first time the function is actually run.
        try:
            compile(self.script or "", f"<Agent Function: {self.function_name}>", "exec")
        except SyntaxError as e:
            frappe.throw(f"Script has a syntax error: {e}")

        if "result" not in (self.script or ""):
            frappe.msgprint(
                "Warning: this script doesn't appear to set a `result` variable. "
                "The agent expects one, e.g. result = {\"created\": True, \"name\": doc.name, \"doctype\": \"...\"}.",
                indicator="orange",
                alert=True,
            )

    def on_update(self):
        # Function list is cached in-process (see agent_caller._get_functions) for
        # speed; invalidate it whenever a function is created/edited so changes
        # take effect immediately without a restart.
        frappe.cache().delete_value("frappe_ai:agent_functions")

    def on_trash(self):
        frappe.cache().delete_value("frappe_ai:agent_functions")
