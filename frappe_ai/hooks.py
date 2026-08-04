app_name = "frappe_ai"
app_title = "Frappe AI"
app_publisher = "Zafar"
app_description = "Natural-language agent that proposes and (on approval) creates Frappe/ERPNext documents, via a local GGUF model."
app_email = "zafar.erp@gmail.com"
app_license = "mit"

# Fixtures ---------------------------------------------------------------
# Ships the built-in Agent Function library (see fixtures/agent_function.json)
# on install/migrate.
fixtures = [
    {"doctype": "Agent Function"},
]
