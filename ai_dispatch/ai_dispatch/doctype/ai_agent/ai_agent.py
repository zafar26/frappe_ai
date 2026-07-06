import frappe
from frappe.model.document import Document


class AIAgent(Document):
    def on_update(self):
        # Agent list is cached in-process (see api.get_cached_agents) for
        # speed; invalidate it whenever an agent is created/edited so
        # changes take effect immediately without a restart.
        frappe.cache().delete_value("ai_dispatch:agents")

    def on_trash(self):
        frappe.cache().delete_value("ai_dispatch:agents")
