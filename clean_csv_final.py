#!/usr/bin/env python3
"""
Clean the ir.model.access.csv file by removing entries for models that don't exist.
"""

import os
import csv
import sys


def get_existing_models(models_dir):
    """Get list of existing model names from the models directory."""
    existing_models = set()

    # Skip these files as they're not models
    skip_files = {"__init__.py", "__pycache__"}

    for filename in os.listdir(models_dir):
        if filename in skip_files or not filename.endswith(".py"):
            continue

        # Read the file to find the _name
        filepath = os.path.join(models_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Look for _name = 'model.name'
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("_name ="):
                        # Extract the model name
                        model_name_in_file = line.split("=")[1].strip().strip("'\"")
                        existing_models.add(model_name_in_file)
                        break
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Add known existing models that might not be detected by file scanning
    known_existing_models = {
        # Core Odoo models that are always available
        "res.users",
        "res.partner",
        "res.company",
        "res.groups",
        "ir.model",
        "ir.model.fields",
        "ir.model.access",
        "ir.rule",
        "mail.message",
        "mail.activity",
        "mail.followers",
        "base",
        "web",
        "portal",
        # Records Management models that exist
        "paper.model_bale",  # We confirmed this exists
        "shred.model_bin",  # We confirmed this exists
        "records.location",  # Common models
        "records.container",
        "records.document",
        "records.billing",
        "records.department",
        "naid.audit.log",
        "rm.module.configurator",
        "records.request",
        "records.tag",
        "records.retention.policy",
        "records.approval.workflow",
        "records.storage.box",
        "records.service.type",
        "records.usage.tracking",
        "naid.compliance.checklist",
        "records.digital.scan",
        "naid.operator.certification",
        "records.survey.user.input",
        "shredding.service.bin",
        "records.storage.department.user",
        "naid.risk.assessment",
        "naid.certificate.item",
        "naid.audit.requirement",
        "shredding.service.log",
        "naid.destruction.record",
        "container.access.photo",
        "unlock.service.history",
        "shredding.service.photo",
        "shredding.inventory.batch",
        "records.location.report.wizard",
        "records.retrieval.work.order",
        "naid.certification.level",
        "naid.compliance.checklist.item",
        "container.access.visitor",
        "naid.training.requirement",
        "mobile.dashboard.widget",
        "naid.performance.history",
        "records.container.log",
        "naid.compliance.action.plan",
        "mobile.dashboard.widget.category",
        "naid.compliance.policy",
        "work.order.coordinator",
        "workflow.visualization.manager",
        "paper.bale.line",
        "naid.compliance.alert",
        "shredding.service.event",
        "naid.equipment.standard",
        "records.approval.workflow.line",
        "naid.custody.event",
        "records.deletion.request",
        "file.retrieval.item",
        "records.inventory.dashboard",
        "records.bulk.user.import",
        "advanced.billing",
        "advanced.billing.contact",
        "advanced.billing.line",
        "advanced.billing.profile",
        "advanced.billing.service.line",
        "advanced.billing.storage.line",
        "approval.history",
        "barcode.generation.history",
        "barcode.models.enhanced",
        "barcode.pricing.tier",
        "barcode.product",
        "barcode.storage.box",
        "base.rate",
        "base.rates",
        "billing.period",
        "bin.barcode.inventory",
        "bin.key",
        "bin.key.history",
        "bin.key.unlock.service",
        "bin.unlock.service",
        "chain.of.custody",
        "container.access.activity",
        "container.access.document",
        "container.access.report",
        "container.access.work.order",
        "container.content",
        "container.destruction.work.order",
        "container.retrieval",
        "container.retrieval.work.order",
        "cross.department.sharing",
        "cross.department.sharing.rule",
        "custody.transfer.event",
        "customer.category",
        "customer.feedback",
        "customer.inventory",
        "customer.inventory.report",
        "customer.inventory.report.line",
        "customer.negotiated.rate",
        "customer.negotiated.rates",
        "customer.portal.diagram",
        "description",
        "destruction.item",
        "discount.rule",
        "display_name",
        "document.retrieval.item",
        "document.search.attempt",
        "feedback.improvement.area",
        "field.label.customization",
        "file.retrieval",
        "file.retrieval.work.order",
        "file.retrieval.work.order.item",
        "full.customization.name",
        "hard.drive.scan.wizard",
        "hr.employee",
        "inventory.adjustment.reason",
        "inventory.item",
        "inventory.item.destruction",
        "inventory.item.destruction.line",
        "inventory.item.location.transfer",
        "inventory.item.profile",
        "inventory.item.retrieval",
        "inventory.item.retrieval.line",
        "inventory.item.type",
        "invoice.generation.log",
        "key.inventory",
        "load",
        "location.group",
        "maintenance.equipment",
        "maintenance.team",
        "media.type",
        "mobile.bin.key.wizard",
        "mobile.photo",
        "naid.certificate",
        "naid.custody",
        "paper.bale",
        "paper.bale.inspection",
        "paper.bale.inspection.wizard",
        "paper.bale.movement",
        "paper.bale.weigh.wizard",
        "payment.split",
        "pickup.location",
        "pickup.request",
        "pickup.route",
        "pickup.schedule.wizard",
        "portal.feedback",
        "portal.request",
        "processing.log",
        "product.container.type",
        "records.audit.log",
        "records.category",
        "records.container.type.converter",
        "records.department.sharing",
        "records.destruction",
        "records.destruction.job",
        "records.installer",
        "records.location.inspection",
        "records.promotional.discount",
        "records.request.line",
        "records.request.type",
        "records.retention.policy.version",
        "records.series",
        "report.records_management.report_customer_inventory",
        "report.records_management.report_location_utilization",
        "report.records_management.revenue_forecasting_report",
        "required.document",
        "retrieval.item.base",
        "retrieval.metric",
        "revenue.analytic",
        "revenue.forecast",
        "route.optimizer",
        "scan.retrieval",
        "service.item",
        "shred.bin",
        "shredding.certificate",
        "shredding.hard_drive",
        "shredding.rate",
        "shredding.service",
        "shredding.team",
        "signed.document",
        "stock.move.sms.validation",
        "temp.inventory",
        "temp.inventory.reject.wizard",
        "transitory.item",
    }

    existing_models.update(known_existing_models)

    return existing_models


def clean_csv(csv_path, existing_models):
    """Clean the CSV file by removing entries for non-existent models."""
    cleaned_rows = []
    removed_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Read header
        cleaned_rows.append(header)

        for row in reader:
            if not row or len(row) < 3:
                continue

            model_id = row[2]  # model_id:id column

            if model_id in existing_models:
                cleaned_rows.append(row)
            else:
                removed_count += 1
                print(f"Removing entry for non-existent model: {model_id}")

    # Write cleaned CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)

    print(f"\nCleaned CSV file: removed {removed_count} entries for non-existent models")
    print(f"Remaining entries: {len(cleaned_rows) - 1}")  # Subtract header

    return removed_count


def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")

    models_dir = os.path.join(script_dir, "records_management", "models")
    csv_path = os.path.join(script_dir, "records_management", "security", "ir.model.access.csv")

    print(f"Models directory: {models_dir}")
    print(f"CSV path: {csv_path}")

    if not os.path.exists(models_dir):
        print(f"Models directory not found: {models_dir}")
        sys.exit(1)

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    print("Scanning existing models...")
    existing_models = get_existing_models(models_dir)
    print(f"Found {len(existing_models)} existing models")

    print("\nCleaning CSV file...")
    removed_count = clean_csv(csv_path, existing_models)

    print("\n✅ CSV cleaning completed successfully!")
    print(f"📊 Summary: Removed {removed_count} entries for non-existent models")


if __name__ == "__main__":
    main()
