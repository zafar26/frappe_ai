from . import __version__ as app_version  # noqa: F401

app_name = "ai_dispatch"
app_title = "AI Dispatch"
app_publisher = "Mohammed Qutubuddin Zafar"
app_description = "Multi-agent RAG system with neural-network-based query routing, built as a Frappe app."
app_email = "mohammedzafar088@gmail.com"
app_license = "MIT"

# Include js, css files in header of desk.html
# app_include_css = "/assets/ai_dispatch/css/ai_dispatch.css"
# app_include_js = "/assets/ai_dispatch/js/ai_dispatch.js"

# Website route rules -- not required, since the www/ai-dispatch folder
# is automatically served at /ai-dispatch, but kept here for clarity /
# in case the route is customized later.
# website_route_rules = [
#     {"from_route": "/dispatch", "to_route": "ai-dispatch"},
# ]

# Fixtures -- ship default agents + starter training examples with the app
# so a fresh install has something to demo immediately.
fixtures = [
    {"doctype": "AI Agent"},
    {"doctype": "Router Training Example"},
]

# Custom bench commands: `bench --site <site> train-router`
commands = "ai_dispatch.commands.commands"
