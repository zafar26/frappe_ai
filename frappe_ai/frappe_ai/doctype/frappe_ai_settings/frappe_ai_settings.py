from frappe.model.document import Document


class FrappeAISettings(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        agent_caller_gguf_path: DF.Data | None
        agent_caller_system_prompt: DF.LongText | None
    # end: auto-generated types

    pass
