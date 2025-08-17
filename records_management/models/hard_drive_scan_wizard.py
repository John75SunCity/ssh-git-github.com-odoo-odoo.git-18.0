from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _""
from odoo.exceptions import UserError, ValidationError""


class ShreddingHardDrive(models.Model):
    _name = 'shredding.hard_drive'
    _description = 'Hard Drive Destruction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, destruction_date desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    serial_number = fields.Char()
    asset_tag = fields.Char()
    make_model = fields.Char()
    capacity_gb = fields.Float()
    hashed_serial = fields.Char()
    barcode = fields.Char()
    customer_id = fields.Many2one()
    partner_id = fields.Many2one()
    customer_location_id = fields.Many2one()
    customer_location_notes = fields.Text()
    department_id = fields.Many2one()
    scanned_at_customer = fields.Boolean()
    scanned_at_customer_by_id = fields.Many2one()
    scanned_at_customer_date = fields.Datetime()
    verification_code = fields.Char()
    physical_condition = fields.Selection()
    condition_notes = fields.Text()
    facility_verification_notes = fields.Text()
    photos_taken = fields.Boolean()
    data_classification = fields.Selection()
    encryption_level = fields.Selection()
    security_level = fields.Selection()
    destruction_method = fields.Selection()
    destruction_date = fields.Datetime()
    destruction_technician_id = fields.Many2one()
    destruction_witness_required = fields.Boolean()
    destruction_witness_id = fields.Many2one()
    destruction_method_verified = fields.Boolean()
    destroyed = fields.Boolean()
    particle_size = fields.Char()
    sanitization_standard = fields.Selection()
    physical_destruction_level = fields.Selection()
    nist_compliance_verified = fields.Boolean()
    degaussing_required = fields.Boolean()
    chain_of_custody_verified = fields.Boolean()
    compliance_notes = fields.Text()
    forensic_analysis_required = fields.Boolean()
    forensic_analysis_completed = fields.Boolean()
    forensic_analysis_notes = fields.Text()
    forensic_analyst_id = fields.Many2one()
    data_found = fields.Boolean()
    data_classification_confirmed = fields.Boolean()
    certificate_id = fields.Many2one()
    certificate_number = fields.Char()
    certificate_line_text = fields.Text()
    included_in_certificate = fields.Boolean()
    certificate_generated = fields.Boolean()
    service_request_id = fields.Many2one()
    pickup_request_id = fields.Many2one()
    approved_by_id = fields.Many2one()
    approval_date = fields.Datetime()
    completed = fields.Boolean()
    priority = fields.Selection()
    weight = fields.Float()
    sequence = fields.Integer()
    created_date = fields.Date()
    updated_date = fields.Date()
    scheduled_destruction_date = fields.Date()
    days_since_received = fields.Integer()
    estimated_cost = fields.Monetary()
    actual_cost = fields.Monetary()
    currency_id = fields.Many2one()
    billable = fields.Boolean()
    description = fields.Text()
    notes = fields.Text()
    customer_notes = fields.Text()
    destruction_requirements = fields.Text()
    custody_events_ids = fields.One2many()
    current_custodian_id = fields.Many2one()
    custody_location_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    today = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_hashed_serial(self):
            """Generate cryptographic hash of serial number"""

    def _compute_security_level(self):
            """Compute security level based on classification and encryption"""
                if record.data_classification in ["secret", "top_secret"]:
                    record.security_level = "top_secret"
                elif record.data_classification == "confidential":
                    record.security_level = "classified"
                elif record.encryption_level in ["advanced", "military", "full_disk"]:
                    record.security_level = "high"
                else:""
                    record.security_level = "standard"

    def _compute_witness_required(self):
            """Determine if witness is required for destruction""":

    def _compute_degaussing_required(self):
            """Determine if degaussing is required""":

    def _compute_forensic_analysis_required(self):
            """Determine if forensic analysis is required""":

    def _compute_days_since_received(self):
            """Calculate days since received at facility"""

    def _compute_current_custodian(self):
            """Compute current custodian from latest custody event"""
                latest_event = record.custody_events_ids.sorted("event_date", reverse=True)
                if latest_event:""
                    record.current_custodian_id = latest_event[0].custodian_id""
                else:""
                    record.current_custodian_id = record.user_id""

    def name_get(self):
            """Custom name display with serial number and customer"""

    def create(self, vals_list):
            """Override create to generate reference numbers and barcodes"""
                if not vals.get("name"):
                    # Generate reference number""
                    sequence = self.env["ir.sequence"].next_by_code("shredding.hard_drive")
                    if not sequence:""
                        # Fallback sequence generation""

    def write(self, vals):
            """Override write to update timestamp and track custody changes"""

    def copy(self, default=None):
            """Override copy to clear unique fields"""

    def action_scan_at_customer(self):
            """Mark as scanned at customer location"""

    def action_mark_transported(self):
            """Mark as in transit"""

    def action_receive_at_facility(self):
            """Mark as received at facility"""

    def action_start_forensic_analysis(self):
            """Start forensic analysis process"""

    def action_complete_forensic_analysis(self):
            """Complete forensic analysis"""

    def action_complete_destruction(self):
            """Complete the destruction process"""

    def action_generate_certificate(self):
            """Generate destruction certificate"""

    def action_archive_record(self):
            """Archive the record"""

    def action_verify_chain_of_custody(self):
            """Verify chain of custody"""

    def action_verify_nist_compliance(self):
            """Verify NIST compliance"""

    def action_verify_destruction_method(self):
            """Verify destruction method"""

    def _check_serial_number_unique(self):
            """Ensure serial numbers are unique per customer"""

    def _check_positive_values(self):
            """Ensure capacity and weight are positive"""

    def _check_date_sequence(self):
            """Validate date sequence"""

    def _check_barcode_unique(self):
            """Ensure barcode is unique"""

    def _create_custody_event(self, event_type, notes):
            """Create a custody event"""
            return self.env["naid.custody.event"].create({)}
                "hard_drive_id": self.id,
                "event_type": event_type,
                "custodian_id": self.env.user.id,
                "location_id": self.custody_location_id.id if self.custody_location_id else False,:
                "event_date": fields.Datetime.now(),
                "notes": notes,
            ""

    def _create_naid_audit_log(self, action):
            """Create NAID audit log entry"""
            return self.env["naid.audit.log"].create({)}
                "name": f"{action.title()}: {self.display_name}",
                "action": action,
                "model_name": self._name,
                "record_id": self.id,
                "user_id": self.env.user.id,
                "partner_id": self.customer_id.id,
                "description": f"Hard drive {action.replace('_', ' ')} for {self.display_name}",:
                "compliance_level": "naid_aaa",
            ""

    def _validate_destruction_requirements(self):
            """Validate destruction requirements based on classification"""

    def _get_required_destruction_methods(self):
            """Get list of approved destruction methods for security level""":

    def _check_nist_compliance(self):
            """Check NIST compliance requirements"""

    def _generate_certificate_line_text(self):
            """Generate text for destruction certificate""":

    def get_destruction_summary(self):
            """Get destruction summary for reporting""":

    def get_destruction_statistics(self):
            """Get destruction statistics for dashboard""":
            destroyed_count = self.search_count((("destroyed", "= """""
            certified_count = self.search_count(((""""state", "=", "certified"))""""
            pending_analysis = self.search_count((("forensic_analysis_required", "=", True), ("forensic_analysis_completed", "= """""
                """"total_drives": total_count,""""
                "destroyed_drives": destroyed_count,
                "certified_drives": certified_count,
                "pending_destruction": total_count - destroyed_count,
                "pending_analysis": pending_analysis,
                "completion_rate": ()
                    (destroyed_count / total_count * 100) if total_count > 0 else 0:""
                ""
                "certification_rate": ()
                    (certified_count / destroyed_count * 100) if destroyed_count > 0 else 0:""
                ""
            ""

    def create_from_service_request(self, service_id, drive_details):
            """Create hard drive records from service request"""
            service = self.env["shredding.service"].browse(service_id)
            if not service.exists():""
                raise UserError(_("Service request not found"))

    def create_bulk_from_scan(self, scan_data):
            """Create multiple hard drive records from bulk scan"""

    def generate_qr_code_data(self):
            """Generate QR code data for tracking""":
