
app_name = "frappe_ai"
app_title = "Frappe AI"
app_publisher = "Mohammed Qutubuddin Zafar"
app_description = "Multi-agent RAG system with neural-network-based query routing, built as a Frappe app."
app_email = "mohammedzafar088@gmail.com"
app_license = "MIT"

# Include js, css files in header of desk.html
# app_include_css = "/assets/frappe_ai/css/frappe_ai.css"
# app_include_js = "/assets/frappe_ai/js/frappe_ai.js"

# Website route rules -- not required, since the www/frappe-ai folder
# is automatically served at /frappe-ai, but kept here for clarity /
# in case the route is customized later.
# website_route_rules = [
#     {"from_route": "/dispatch", "to_route": "frappe-ai"},
# ]

# Fixtures -- ship default agents + starter training examples with the app
# so a fresh install has something to demo immediately.
fixtures = [
    {"doctype": "Agent Function"},
]