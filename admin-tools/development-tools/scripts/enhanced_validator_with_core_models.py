#!/usr/bin/env python3
"""
Enhanced XML validator that includes core Odoo models to eliminate dependency warnings
"""

import sys
import os
from pathlib import Path
from collections import defaultdict

# Import the base validator
sys.path.insert(0, os.path.dirname(__file__))
from advanced_xml_model_validator import OdooFieldExtractor, XMLDataValidator


class CoreOdooModelProvider:
    """Provides core Odoo model definitions"""

    @staticmethod
    def get_core_models():
        """Return core Odoo models with commonly used fields"""
        return {
            # Mail module models
            "mail.template": {
                "name": True,
                "subject": True,
                "body_html": True,
                "email_from": True,
                "email_to": True,
                "model": True,
                "model_id": True,
                "partner_to": True,
                "auto_delete": True,
                "use_default_to": True,
                "lang": True,
                "user_signature": True,
                "report_name": True,
                "report_template": True,
                "ref_ir_act_window": True,
                "attachment_ids": True,
                "email_cc": True,
                "email_bcc": True,
                "reply_to": True,
                "mail_server_id": True,
                "scheduled_date": True,
            },
            # SMS module models
            "sms.template": {
                "name": True,
                "model": True,
                "model_id": True,
                "body": True,
                "lang": True,
                "sidebar_action_id": True,
            },
            # Product module models
            "product.product": {
                "name": True,
                "default_code": True,
                "barcode": True,
                "categ_id": True,
                "type": True,
                "list_price": True,
                "standard_price": True,
                "sale_ok": True,
                "purchase_ok": True,
                "active": True,
                "company_id": True,
                "uom_id": True,
                "uom_po_id": True,
                "description": True,
                "description_purchase": True,
                "description_sale": True,
                "weight": True,
                "volume": True,
                "taxes_id": True,
                "supplier_taxes_id": True,
                "property_account_income_id": True,
                "property_account_expense_id": True,
            },
            # Survey module models
            "survey.survey": {
                "title": True,
                "description": True,
                "certification": True,
                "certification_mail_template_id": True,
                "certification_report_layout": True,
                "users_login_required": True,
                "users_can_go_back": True,
                "questions_layout": True,
                "progression_mode": True,
                "session_code": True,
                "access_mode": True,
                "access_token": True,
                "is_attempts_limited": True,
                "attempts_limit": True,
                "is_time_limited": True,
                "time_limit": True,
                "scoring_type": True,
                "scoring_success_min": True,
                "certification_give_badge": True,
                "certification_badge_id": True,
                "state": True,
                "active": True,
                "company_id": True,
            },
            "survey.question": {
                "title": True,
                "description": True,
                "question_type": True,
                "sequence": True,
                "page_id": True,
                "survey_id": True,
                "is_page": True,
                "questions_selection": True,
                "random_questions_count": True,
                "constr_mandatory": True,
                "constr_error_msg": True,
                "matrix_subtype": True,
                "column_nb": True,
                "comments_allowed": True,
                "comments_message": True,
                "comment_count_as_answer": True,
                "save_as_email": True,
                "save_as_nickname": True,
                "is_scored_question": True,
                "answer_score": True,
                "background_image": True,
                # Add validation fields
                "validation_min_float_value": True,
                "validation_max_float_value": True,
                "validation_error_msg": True,
            },
            "survey.question.answer": {
                "value": True,
                "sequence": True,
                "question_id": True,
                "matrix_question_id": True,
                "is_correct": True,
                "answer_score": True,
                "value_image": True,
            },
        }


class EnhancedXMLValidator:
    """Enhanced validator with core Odoo models"""

    def __init__(self):
        # Create the field extractor for custom models
        self.field_extractor = OdooFieldExtractor()

        # Add core Odoo models
        core_models = CoreOdooModelProvider.get_core_models()
        for model_name, fields in core_models.items():
            self.field_extractor.models[model_name] = fields
            self.field_extractor.field_types[model_name] = {}

    def load_custom_models(self):
        """Load all custom records_management models"""
        records_path = Path(
            "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
        )

        model_files_processed = 0
        for model_dir in ["models", "wizards"]:
            model_path = records_path / model_dir
            if model_path.exists():
                for py_file in model_path.glob("*.py"):
                    if py_file.name != "__init__.py":
                        self.field_extractor.parse_model_file(py_file)
                        model_files_processed += 1

        return model_files_processed

    def validate_all_files(self):
        """Validate all XML files"""
        records_path = Path(
            "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
        )

        # Load custom models
        model_files_processed = self.load_custom_models()

        print(f"📊 Phase 1: Loaded {model_files_processed} custom model files")
        print(f"✅ Total models available: {len(self.field_extractor.models)}")

        # Create validator
        validator = XMLDataValidator(self.field_extractor)

        # Validate all XML files
        all_warnings = []
        all_errors = []

        for data_dir in ["data", "demo"]:
            data_path = records_path / data_dir
            if data_path.exists():
                for xml_file in data_path.glob("*.xml"):
                    errors, warnings = validator.validate_xml_file(xml_file)
                    all_errors.extend(errors)
                    all_warnings.extend(warnings)

        return all_errors, all_warnings


def main():
    print("🔍 Enhanced XML Validator with Core Odoo Models")
    print("=" * 60)

    validator = EnhancedXMLValidator()
    errors, warnings = validator.validate_all_files()

    print(f"\n🎉 VALIDATION COMPLETE")
    print("=" * 40)
    print(f"Field errors found: {len(errors)}")
    print(f"Warnings found: {len(warnings)}")

    if errors:
        print(f"\n❌ FIELD ERRORS FOUND: {len(errors)}")
        print("=" * 50)

        errors_by_model = defaultdict(list)
        for error in errors:
            errors_by_model[error["model"]].append(error)

        for model_name, model_errors in errors_by_model.items():
            print(f"\n🔹 Model: {model_name} ({len(model_errors)} errors)")

            for error in model_errors:
                print(f"   ❌ File: {error['file']}")
                print(f"      Record: {error['record_id']}")
                print(f"      Invalid field: '{error['field']}'")
                if error.get("line"):
                    print(f"      Line: {error['line']}")
                if error.get("suggestions"):
                    print(f"      Suggestions: {', '.join(error['suggestions'])}")
                print()

    if warnings:
        print(f"\n⚠️  REMAINING WARNINGS: {len(warnings)}")
        print("=" * 50)

        warnings_by_file = defaultdict(list)
        for warning in warnings:
            warnings_by_file[warning["file"]].append(warning)

        for file_name, file_warnings in warnings_by_file.items():
            print(f"\n📁 File: {file_name} ({len(file_warnings)} warnings)")

            for warning in file_warnings:
                print(f"   ⚠️  Record: {warning['record_id']}")
                print(f"      Model: {warning['model']}")
                print(f"      Issue: {warning.get('issue', 'Unknown')}")
                print()
    else:
        print("✅ All warnings resolved!")


if __name__ == "__main__":
    main()
