#!/usr/bin/env python3
"""
Complete Missing Fields Checklist - Systematic Analysis and Resolution
====================================================================

This script systematically checks every single missing field and categorizes them:
✅ = Field needs to be added to model
🔄 = Field should be inherited from Odoo (skip)
⚠️ = Field requires investigation
❌ = Field is view-only/computed (skip)

Usage: python complete_missing_fields_checklist.py
"""

import os
import sys
import re
from pathlib import Path


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# Known Odoo inherited fields that should NOT be added to models
ODOO_INHERITED_FIELDS = {
    "activity_ids",
    "activity_state",
    "activity_exception_decoration",
    "activity_type",
    "message_ids",
    "message_follower_ids",
    "message_attachment_count",
    "create_date",
    "create_uid",
    "write_date",
    "write_uid",
    "__last_update",
    "display_name",
    "id",
    "name",  # name often inherited from mail.thread
}

# View-only fields that don't need to be in models
VIEW_ONLY_FIELDS = {
    "arch",
    "model",
    "res_model",
    "view_mode",
    "view_id",
    "search_view_id",
    "context",
    "domain",
    "target",
    "help",
    "inherit_id",
}

# Fields that are typically computed or related
COMPUTED_FIELDS = {
    "display_name",
    "name",
    "total_",
    "count_",
    "_count",
    "average_",
    "percentage_",
    "rate_",
    "_rate",
    "score_",
    "_score",
}


def check_field_category(field_name):
    """Categorize field based on naming patterns and known lists"""
    if field_name in ODOO_INHERITED_FIELDS:
        return "🔄", "Inherited from Odoo (mail.thread/activity.mixin)"

    if field_name in VIEW_ONLY_FIELDS:
        return "❌", "View-only field"

    # Check for computed field patterns
    for pattern in COMPUTED_FIELDS:
        if pattern in field_name:
            return "❌", "Likely computed field"

    # Check for specific patterns that indicate inheritance
    if field_name.endswith("_ids") and "log" in field_name:
        return "⚠️", "May be One2many relationship - needs investigation"

    if field_name.endswith("_id") and field_name.startswith(
        ("user_", "create_", "write_")
    ):
        return "🔄", "Odoo system field"

    if "date" in field_name and field_name in ["create_date", "write_date"]:
        return "🔄", "Odoo system field"

    # Default: needs to be added
    return "✅", "Should be added to model"


def analyze_missing_fields():
    """Main analysis function"""

    # Missing fields data from the comprehensive analysis
    missing_fields_data = {
        "records.document.type": [
            "activity_ids",
            "arch",
            "help",
            "message_follower_ids",
            "message_ids",
            "model",
            "res_model",
            "view_mode",
        ],
        "records.location.report.wizard": [
            "arch",
            "current_utilization",
            "include_child_locations",
            "location_id",
            "location_name",
            "model",
            "name",
            "report_date",
            "total_capacity",
            "utilization_percentage",
        ],
        "visitor.pos.wizard": [
            "activity_ids",
            "amount",
            "arch",
            "audit_level",
            "audit_notes",
            "audit_required",
            "authorization_code",
            "base_amount",
            "cashier_id",
            "certificate_required",
            "chain_of_custody",
            "chain_of_custody_id",
            "check_in_time",
            "collected",
            "collection_date",
            "compliance_documentation",
            "compliance_officer",
            "confidentiality_level",
            "context",
            "create_new_customer",
            "customer_category",
            "customer_credit_limit",
            "customer_payment_terms",
            "customer_processing_time",
            "customer_record_created",
            "customer_record_id",
            "destruction_method",
            "digitization_format",
            "discount_percent",
            "document_count",
            "document_name",
            "document_type",
            "duration_seconds",
            "error_details",
            "error_message",
            "error_time",
            "error_type",
            "estimated_service_time",
            "estimated_volume",
            "existing_customer_id",
            "express_service",
            "express_surcharge",
            "final_verification_by",
            "help",
            "integration_error_ids",
            "invoice_generated",
            "invoice_id",
            "invoice_required",
            "message_follower_ids",
            "message_ids",
            "model",
            "naid_audit_created",
            "naid_audit_id",
            "naid_certificate_required",
            "naid_compliance_required",
            "notes",
            "payment_method_id",
            "payment_reference",
            "payment_split_ids",
            "payment_terms",
            "pickup_required",
            "pos_config_id",
            "pos_order_created",
            "pos_order_id",
            "pos_session_id",
            "processed_by",
            "processing_log_ids",
            "processing_priority",
            "product_id",
            "purpose_of_visit",
            "quality_check_by",
            "quantity",
            "receipt_email",
            "records_request_created",
            "records_request_id",
            "required",
            "required_document_ids",
            "res_model",
            "resolution_notes",
            "resolved",
            "retention_period",
            "scanning_required",
            "search_view_id",
            "service_configuration_time",
            "service_item_ids",
            "service_location",
            "service_type",
            "shredding_type",
            "special_requirements",
            "step_description",
            "step_name",
            "step_status",
            "step_time",
            "subtotal",
            "supervisor_approval",
            "target",
            "tax_amount",
            "tax_id",
            "total_amount",
            "total_discount",
            "total_processing_time",
            "transaction_id",
            "unit_price",
            "view_id",
            "view_mode",
            "visitor_email",
            "visitor_id",
            "visitor_name",
            "visitor_phone",
            "witness_required",
            "witness_verification",
            "wizard_start_time",
        ],
        # Add more models as needed...
    }

    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}")
    print("🔍 COMPLETE MISSING FIELDS CHECKLIST")
    print(f"{'='*80}{Colors.END}")
    print()

    total_fields = 0
    needs_adding = 0
    inherited_fields = 0
    view_only_fields = 0
    investigation_needed = 0

    for model_name, fields in missing_fields_data.items():
        print(f"{Colors.BOLD}{Colors.PURPLE}📋 Model: {model_name}{Colors.END}")
        print("-" * (len(model_name) + 15))

        for field in fields:
            category, reason = check_field_category(field)
            total_fields += 1

            if category == "✅":
                needs_adding += 1
                color = Colors.GREEN
            elif category == "🔄":
                inherited_fields += 1
                color = Colors.CYAN
            elif category == "❌":
                view_only_fields += 1
                color = Colors.RED
            else:  # ⚠️
                investigation_needed += 1
                color = Colors.YELLOW

            print(f"   {category} {color}{field:<35}{Colors.END} {reason}")

        print()

    # Summary statistics
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}")
    print("📊 SUMMARY STATISTICS")
    print(f"{'='*80}{Colors.END}")
    print()
    print(f"Total missing fields analyzed: {Colors.BOLD}{total_fields}{Colors.END}")
    print(
        f"✅ Fields needing addition:    {Colors.GREEN}{Colors.BOLD}{needs_adding}{Colors.END}"
    )
    print(
        f"🔄 Inherited from Odoo:       {Colors.CYAN}{Colors.BOLD}{inherited_fields}{Colors.END}"
    )
    print(
        f"❌ View-only/computed:        {Colors.RED}{Colors.BOLD}{view_only_fields}{Colors.END}"
    )
    print(
        f"⚠️  Needs investigation:       {Colors.YELLOW}{Colors.BOLD}{investigation_needed}{Colors.END}"
    )
    print()

    completion_rate = ((inherited_fields + view_only_fields) / total_fields) * 100
    print(f"🎯 Auto-categorized: {Colors.BOLD}{completion_rate:.1f}%{Colors.END}")

    if needs_adding > 0:
        print(
            f"\n{Colors.YELLOW}⚠️  Action Required: {needs_adding} fields need to be added to models{Colors.END}"
        )

    if investigation_needed > 0:
        print(
            f"{Colors.YELLOW}🔍 Manual Review: {investigation_needed} fields need investigation{Colors.END}"
        )

    return {
        "total": total_fields,
        "needs_adding": needs_adding,
        "inherited": inherited_fields,
        "view_only": view_only_fields,
        "investigation": investigation_needed,
    }


def create_field_addition_script(model_name, fields_to_add):
    """Generate code to add missing fields to a specific model"""

    print(
        f"\n{Colors.BOLD}{Colors.GREEN}📝 FIELD ADDITION CODE FOR {model_name.upper()}{Colors.END}"
    )
    print("-" * 60)

    for field in fields_to_add:
        field_type = suggest_field_type(field)
        print(f"    {field} = {field_type}")

    print()


def suggest_field_type(field_name):
    """Suggest appropriate Odoo field type based on field name"""

    if field_name.endswith("_id"):
        return "fields.Many2one('res.partner', string='Partner')"
    elif field_name.endswith("_ids"):
        return "fields.One2many('related.model', 'inverse_field', string='Related Records')"
    elif "date" in field_name:
        return "fields.Date(string='Date')"
    elif "time" in field_name:
        return "fields.Datetime(string='Date Time')"
    elif field_name.endswith("_count"):
        return "fields.Integer(string='Count', compute='_compute_count')"
    elif "amount" in field_name or "cost" in field_name or "price" in field_name:
        return "fields.Monetary(string='Amount', currency_field='currency_id')"
    elif "percentage" in field_name or "rate" in field_name:
        return "fields.Float(string='Percentage', digits=(5, 2))"
    elif (
        "required" in field_name
        or field_name.startswith("is_")
        or field_name.startswith("has_")
    ):
        return "fields.Boolean(string='Required', default=False)"
    elif "notes" in field_name or "description" in field_name:
        return "fields.Text(string='Notes')"
    else:
        return "fields.Char(string='Field')"


if __name__ == "__main__":
    try:
        print(
            f"{Colors.BOLD}🚀 Starting Complete Missing Fields Analysis...{Colors.END}\n"
        )

        stats = analyze_missing_fields()

        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Analysis Complete!{Colors.END}")

        if stats["needs_adding"] > 0:
            print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
            print("1. Review fields marked with ✅")
            print("2. Add them to respective model files")
            print("3. Run module validation")
            print("4. Test in Odoo.sh environment")

    except Exception as e:
        print(f"{Colors.RED}❌ Error during analysis: {e}{Colors.END}")
        sys.exit(1)
