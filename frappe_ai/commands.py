import click
import frappe


@click.command("train-router")
@click.option("--site", required=True)
def train_router_command(site):
    """Train the Frappe AI router classifier from Router Training Example records."""
    frappe.init(site=site)
    frappe.connect()
    try:
        from frappe_ai.router.train import train_router

        result = train_router()
        click.echo(f"Trained router on {result['num_examples']} examples.")
        click.echo(f"Labels: {result['labels']}")
        click.echo(f"Validation accuracy: {result['final_val_accuracy']:.2%}")
    finally:
        frappe.destroy()


commands = [train_router_command]
