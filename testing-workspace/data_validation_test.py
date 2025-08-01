"""
DATA FILE VALIDATION USING ODOO EXTENSIONS
Testing approach: Paste data file content and let extensions validate field references
"""

# Let me create test model files to validate against the data files
# This will help the extensions identify missing fields and validation issues

from odoo import models, fields, api


# Test model for naid.compliance (from naid_compliance_data.xml)
class TestNaidCompliance(models.Model):
    _name = "naid.compliance"
    _description = "NAID Compliance Test Model"

    # Fields referenced in naid_compliance_data.xml - let extensions validate these
    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence")
    policy_type = fields.Selection(
        [
            ("access_control", "Access Control"),
            ("document_handling", "Document Handling"),
            ("destruction", "Destruction"),
            ("employee_screening", "Employee Screening"),
            ("facility_security", "Facility Security"),
            ("equipment", "Equipment"),
            ("audit", "Audit"),
        ],
        string="Policy Type",
    )
    description = fields.Text(string="Description")
    mandatory = fields.Boolean(string="Mandatory")
    automated_check = fields.Boolean(string="Automated Check")
    check_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("per_operation", "Per Operation"),
        ],
        string="Check Frequency",
    )
    implementation_notes = fields.Text(string="Implementation Notes")
    violation_consequences = fields.Text(string="Violation Consequences")
    review_frequency_months = fields.Integer(string="Review Frequency (Months)")


# Test model for records.location (from model_records.xml error)
class TestRecordsLocation(models.Model):
    _name = "records.location"
    _description = "Records Location Test Model"

    # Fields that were causing the error - let extensions validate
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("secure", "Secure Storage"),
            ("temporary", "Temporary"),
        ],
        string="Location Type",
    )
    building = fields.Char(string="Building")
    zone = fields.Char(string="Zone")
    active = fields.Boolean(string="Active", default=True)
    climate_controlled = fields.Boolean(string="Climate Controlled")
    access_level = fields.Selection(
        [
            ("public", "Public"),
            ("restricted", "Restricted"),
            ("secure", "Secure"),
            ("high_security", "High Security"),
        ],
        string="Access Level",
    )
    max_capacity = fields.Integer(string="Max Capacity")


# Test product.product extensions for products.xml validation
class TestProductProduct(models.Model):
    _name = "product.product"
    _inherit = "product.product"

    # Standard product fields that should exist - extensions will validate
    # Let's see if there are any missing field references
    pass


print("Extension validation files created for data validation testing")
