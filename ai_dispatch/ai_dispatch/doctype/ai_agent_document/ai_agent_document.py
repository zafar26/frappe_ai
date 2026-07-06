import frappe
from frappe.model.document import Document

from ai_dispatch.rag.vector_store import add_or_update_document, delete_document


class AIAgentDocument(Document):
    def after_insert(self):
        self._sync_to_vector_store()

    def on_update(self):
        self._sync_to_vector_store()

    def on_trash(self):
        try:
            delete_document(self.agent, self.name)
        except Exception:
            frappe.log_error(
                title="AI Dispatch: failed to remove document from vector store",
                message=frappe.get_traceback(),
            )

    def _sync_to_vector_store(self):
        try:
            add_or_update_document(self.agent, self.name, self.content)
            if not self.embedded:
                frappe.db.set_value(self.doctype, self.name, "embedded", 1, update_modified=False)
        except Exception:
            # Don't block saving the document if the embedding model /
            # vector store isn't available yet -- just log it so the
            # knowledge entry isn't lost, and it can be re-synced later.
            frappe.log_error(
                title="AI Dispatch: failed to embed document",
                message=frappe.get_traceback(),
            )
