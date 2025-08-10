# -*- coding: utf-8 -*-
"""
Shredding Certificate Management Module
This module provides comprehensive shredding certificate management for the Records
Management System. It handles the complete lifecycle of NAID-compliant destruction
certificates with automated generation, witness verification, and audit trail
capabilities for regulatory compliance.
Key Features:
- NAID AAA/AA/A compliant certificate generation
- Automated certificate numbering and sequencing
- Witness verification and signature management
- Multi-method destruction tracking (cross-cut, pulverization, etc.)
- Complete audit trail with mail.thread integration
- Customer portal integration for certificate delivery
Business Processes:
1. Certificate Creation: Automated creation from completed shredding services
2. Compliance Verification: NAID standard compliance validation
3. Witness Management: Witness information capture and verification
4. Certificate Issuance: Formal certificate generation and numbering
5. Delivery Tracking: Certificate delivery status and confirmation
6. Archive Management: Long-term certificate storage and retrieval
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class ShreddingCertificate(models.Model):
    _name = "shredding.certificate"
    _description = "Shredding Certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Certificate Number",
        required=True,
        tracking=True,
        index=True,
        help="Unique certificate identification number",
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this certificate",
    
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("delivered", "Delivered"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current certificate status",
    

    # ============================================================================
    # CERTIFICATE DETAILS
    # ============================================================================
    certificate_date = fields.Date(
        string="Certificate Date",
        default=fields.Date.today,
        required=True,
        tracking=True,
        help="Date the certificate was issued",
    
    destruction_date = fields.Date(
        string="Destruction Date",
        required=True,
        tracking=True,
        help="Date when destruction occurred",
    
    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut Shredding"),
            ("strip_cut", "Strip Cut Shredding"),
            ("pulverization", "Pulverization"),
            ("incineration", "Incineration"),
            ("degaussing", "Degaussing"),
            ("disintegration", "Disintegration"),
            ("acid_bath", "Acid Bath"),
        ],
        string="Destruction Method",
        required=True,
        tracking=True,
        help="Method used for document destruction",
    

    # ============================================================================
    # CUSTOMER & SERVICE INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer for whom the destruction was performed",
    
    customer_contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        domain="[('parent_id', '=', partner_id)]",
        help="Primary customer contact for this certificate",
    
    service_location = fields.Char(
        string="Service Location",
        help="Location where destruction service was performed",
    
    equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Shredding Equipment",
        help="Equipment used for the destruction service",
    

    # ============================================================================
    # WITNESS INFORMATION
    # ============================================================================
    witness_required = fields.Boolean(
        string="Witness Required",
        default=True,
        help="Whether witness verification is required",
    
    witness_name = fields.Char(
        string="Witness Name", tracking=True, help="Name of the witness to destruction"
    
    witness_title = fields.Char(
        string="Witness Title", help="Title/position of the witness"
    
    witness_company = fields.Char(
        string="Witness Company", help="Company or organization of the witness"
    
    witness_signature_date = fields.Date(
        string="Witness Signature Date",
        tracking=True,
        help="Date witness signed the certificate",
    
    witness_contact_info = fields.Char(
        string="Witness Contact", help="Witness contact information"
    

    # ============================================================================
    # DESTRUCTION METRICS
    # ============================================================================
    total_weight = fields.Float(
        string="Total Weight Destroyed (lbs)",
        digits="Stock Weight",
        default=0.0,
        tracking=True,
        help="Total weight of materials destroyed",
    
    total_containers = fields.Integer(
        string="Total Containers",
        default=0,
        help="Total number of containers destroyed",
    
    total_boxes = fields.Integer(
        string="Total Boxes", default=0, help="Total number of boxes destroyed"
    
    estimated_page_count = fields.Integer(
        string="Estimated Page Count", default=0, help="Estimated total pages destroyed"
    
    destruction_duration = fields.Float(
        string="Destruction Duration (hours)",
        digits=(5, 2),
        help="Time taken for destruction process",
    

    # ============================================================================
    # COMPLIANCE & CERTIFICATION
    # ============================================================================
    naid_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
        ],
        string="NAID Certification Level",
        default="aaa",
        required=True,
        tracking=True,
        help="NAID compliance level for this destruction",
    
    naid_member_id = fields.Char(
        string="NAID Member ID", help="NAID membership identification number"
    
    certification_statement = fields.Text(
        string="Certification Statement",
        default="This is to certify that the documents/materials described above have been destroyed in accordance with NAID standards and all applicable regulations. The destruction was witnessed and verified according to established chain of custody procedures.",
        help="Official certification statement",
    
    compliance_notes = fields.Text(
        string="Compliance Notes", help="Additional compliance and regulatory notes"
    

    # ============================================================================
    # SECURITY & VERIFICATION
    # ============================================================================
    certificate_verified = fields.Boolean(
        string="Certificate Verified",
        default=False,
        tracking=True,
        help="Whether certificate has been verified",
    
    verification_date = fields.Datetime(
        string="Verification Date",
        tracking=True,
        help="Date and time of certificate verification",
    
    verified_by_id = fields.Many2one(
        "res.users",
        string="Verified By",
        tracking=True,
        help="User who verified the certificate",
    
    chain_of_custody_number = fields.Char(
        string="Chain of Custody Number",
        help="Associated chain of custody reference number",
    

    # ============================================================================
    # DELIVERY TRACKING
    # ============================================================================
    delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("portal", "Customer Portal"),
            ("mail", "Physical Mail"),
            ("pickup", "Customer Pickup"),
        ],
        string="Delivery Method",
        default="portal",
        help="Method used to deliver certificate to customer",
    
    delivered_date = fields.Date(
        string="Delivered Date",
        tracking=True,
        help="Date certificate was delivered to customer",
    
    delivered_by_id = fields.Many2one(
        "res.users",
        string="Delivered By",
        tracking=True,
        help="User who delivered the certificate",
    
    delivery_confirmation = fields.Boolean(
        string="Delivery Confirmed",
        default=False,
        tracking=True,
        help="Whether delivery has been confirmed by customer",
    

    # ============================================================================
    # TECHNICAL DETAILS
    # ============================================================================
    destruction_equipment = fields.Char(
        string="Destruction Equipment", help="Equipment used for destruction"
    
    equipment_serial_number = fields.Char(
        string="Equipment Serial Number", help="Serial number of destruction equipment"
    
    operator_name = fields.Char(
        string="Operator Name", help="Name of equipment operator"
    
    temperature_log = fields.Text(
        string="Temperature Log",
        help="Temperature readings during destruction (for incineration)",
    

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    shredding_service_ids = fields.One2many(
        "shredding.service",
        "certificate_id",
        string="Shredding Services",
        help="Shredding services covered by this certificate",
    
    destruction_item_ids = fields.One2many(
        "destruction.item",
        "certificate_id",
        string="Destruction Items",
        help="Individual items destroyed",
    

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    service_count = fields.Integer(
        string="Service Count",
        compute="_compute_service_count",
        store=True,
        help="Number of shredding services on this certificate",
    
    item_count = fields.Integer(
        string="Item Count",
        compute="_compute_item_count",
        store=True,
        help="Number of destruction items",
    

    # ============================================================================
    # AUDIT FIELDS
    # ============================================================================
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
        help="Certificate creation timestamp",
    
    issued_date = fields.Datetime(
        string="Issued Date",
        tracking=True,
        readonly=True,
        help="Date and time certificate was issued",
    
    notes = fields.Text(string="Internal Notes", help="Internal notes and comments")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("shredding_service_ids")
    def _compute_service_count(self):
        """Compute the number of shredding services"""
        for record in self:
            record.service_count = len(record.shredding_service_ids)

    @api.depends("destruction_item_ids")
    def _compute_item_count(self):
        """Compute the number of destruction items"""
        for record in self:
            record.item_count = len(record.destruction_item_ids)

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate certificate numbers"""
        for vals in vals_list:
            if not vals.get("name"):
                # Generate certificate number with sequence
                sequence = self.env["ir.sequence"].next_by_code("shredding.certificate")
                if not sequence:
                    # Fallback sequence generation
                    today = fields.Date.today().strftime("%Y%m%d")
                    count = self.search_count([]) + 1
                    sequence = f"CERT-{today}-{count:04d}"
                vals["name"] = sequence
            vals["created_date"] = fields.Datetime.now()
        return super().create(vals_list)

    def name_get(self):
        """Custom name display with customer and date"""
        result = []
        for record in self:
            name = record.name
            if record.partner_id:
                name = _("%s - %s"
            if record.certificate_date:
                name = _("%s (%s)"
            result.append((record.id, name))
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_issue_certificate(self):
        """Issue the certificate"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft certificates can be issued"))
        if not self.witness_name and self.witness_required:
            raise UserError(
                _("Witness information is required before issuing certificate")
            
        self.write(
            {
                "state": "issued",
                "issued_date": fields.Datetime.now(),
                "certificate_verified": True,
                "verification_date": fields.Datetime.now(),
                "verified_by_id": self.env.user.id,
            }
        
        self.message_post(body=_("Action completed"))body=_("Certificate issued: %s", self.name))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Issued"),
                "message": _("Certificate %s has been issued successfully", self.name),
                "type": "success",
            },
        }

    def action_deliver_certificate(self):
        """Mark certificate as delivered"""
        self.ensure_one()
        if self.state != "issued":
            raise UserError(_("Only issued certificates can be delivered"))
        self.write(
            {
                "state": "delivered",
                "delivered_date": fields.Date.today(),
                "delivered_by_id": self.env.user.id,
                "delivery_confirmation": True,
            }
        
        self.message_post(body=_("Certificate delivered to customer"))
        # Send notification to customer
        if self.partner_id.email:
            self._send_certificate_notification()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Delivered"),
                "message": _("Certificate has been marked as delivered"),
                "type": "success",
            },
        }

    def action_archive_certificate(self):
        """Archive the certificate"""
        self.ensure_one()
        if self.state not in ["delivered"]:
            raise UserError(_("Only delivered certificates can be archived"))
        self.write({"state": "archived"})
        self.message_post(body=_("Certificate archived"))

    def action_reset_to_draft(self):
        """Reset certificate to draft state"""
        self.ensure_one()
        self.write(
            {
                "state": "draft",
                "certificate_verified": False,
                "verification_date": False,
                "verified_by_id": False,
                "issued_date": False,
            }
        
        self.message_post(body=_("Certificate reset to draft"))

    def action_print_certificate(self):
        """Print the certificate"""
        self.ensure_one()
        return self.env.ref(
            "records_management.action_report_shredding_certificate"
        ).report_action(self)

    def action_view_services(self):
        """View related shredding services"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Certificate Services - %s", self.name),
            "res_model": "shredding.service",
            "view_mode": "tree,form",
            "domain": [("certificate_id", "=", self.id)],
            "context": {"default_certificate_id": self.id},
        }

    def action_view_destruction_items(self):
        """View destruction items"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Items - %s", self.name),
            "res_model": "destruction.item",
            "view_mode": "tree,form",
            "domain": [("certificate_id", "=", self.id)],
            "context": {"default_certificate_id": self.id},
        }

    def action_send_to_customer(self):
        """Send certificate to customer via selected delivery method"""
        self.ensure_one()
        if self.state != "issued":
            raise UserError(_("Only issued certificates can be sent to customers"))

        if self.delivery_method == "email":
            return self._send_certificate_email()
        elif self.delivery_method == "portal":
            pass
            return self._make_available_in_portal()
        else:
            pass
            # For mail/pickup, just mark as delivered
            return self.action_deliver_certificate()

    def action_regenerate_certificate(self):
        """Regenerate certificate with updated data"""
        self.ensure_one()
        if self.state in ["delivered", "archived"]:
            raise UserError(_("Cannot regenerate delivered or archived certificates"))

        # Update totals from related services
        self._update_totals_from_services()
        self.message_post(body=_("Certificate data regenerated from services"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Regenerated"),
                "message": _("Certificate data has been updated from related services"),
                "type": "success",
            },
        }

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _send_certificate_notification(self):
        """Send certificate notification to customer"""
        template = self.env.ref(
            "records_management.email_template_shredding_certificate",
            raise_if_not_found=False,
        
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_certificate_email(self):
        """Send certificate via email"""
        if not self.partner_id.email:
            raise UserError(_("Customer email address is required"))

        self._send_certificate_notification()
        self.action_deliver_certificate()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Sent"),
                "message": _("Certificate has been sent via email to %s", self.partner_id.email),
                "type": "success",
            },
        }

    def _make_available_in_portal(self):
        """Make certificate available in customer portal"""
        # Set portal visibility
        self.write({"delivery_method": "portal"})

        # Create portal notification
        self.message_post(body=_("Action completed"))
            body=_("Certificate is now available in customer portal"),
            partner_ids=self.partner_id.ids,
        

        self.action_deliver_certificate()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Portal Updated"),
                "message": _("Certificate is now available in customer portal"),
                "type": "success",
            },
        }

    def _update_totals_from_services(self):
        """Update certificate totals from related services"""
        total_weight = sum(self.shredding_service_ids.mapped("total_weight"))
        total_containers = sum(self.shredding_service_ids.mapped("container_count"))
        total_boxes = sum(self.shredding_service_ids.mapped("total_boxes"))

        self.write(
            {
                "total_weight": total_weight,
                "total_containers": total_containers,
                "total_boxes": total_boxes,
            }
        

    @api.model
    def generate_from_services(self, service_ids):
        """Generate certificate from completed shredding services"""
        services = self.env["shredding.service"].browse(service_ids)

        if not services:
            raise UserError(_("No services provided for certificate generation"))

        # Validate all services are completed
        incomplete_services = services.filtered(lambda s: s.state != "done")
        if incomplete_services:
            raise UserError(
                _("All services must be completed before generating certificate")
            

        # Get common customer
        customers = services.mapped("partner_id")
        if len(customers) > 1:
            raise UserError(_("All services must be for the same customer"))

        # Create certificate
        certificate_vals = {
            "partner_id": customers[0].id,
            "destruction_date": fields.Date.today(),
            "destruction_method": services[0].destruction_method or "cross_cut",
            "naid_level": "aaa",
            "service_location": services[0].service_location,
            "total_weight": sum(services.mapped("total_weight")),
            "total_containers": sum(services.mapped("container_count")),
            "total_boxes": sum(services.mapped("total_boxes")),
        }

        certificate = self.create(certificate_vals)

        # Link services to certificate
        services.write({"certificate_id": certificate.id})

        return certificate

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("destruction_date", "certificate_date")
    def _check_dates(self):
        """Validate certificate and destruction dates"""
        for record in self:
            if record.destruction_date and record.certificate_date:
                pass
                if record.destruction_date > record.certificate_date:
                    raise ValidationError(
                        _("Destruction date cannot be after certificate date")
                    

    @api.constrains("witness_signature_date", "destruction_date")
    def _check_witness_date(self):
        """Validate witness signature date"""
        for record in self:
            if record.witness_signature_date and record.destruction_date:
                pass
                if record.witness_signature_date < record.destruction_date:
                    raise ValidationError(
                        _("Witness signature date cannot be before destruction date")
                    

    @api.constrains("total_weight", "total_containers", "total_boxes")
    def _check_totals(self):
        """Validate certificate totals"""
        for record in self:
            if record.total_weight < 0:
                raise ValidationError(_("Total weight cannot be negative"))
            if record.total_containers < 0:
                raise ValidationError(_("Total containers cannot be negative"))
            if record.total_boxes < 0:
                raise ValidationError(_("Total boxes cannot be negative"))

    @api.constrains("witness_required", "witness_name")
    def _check_witness_info(self):
        """Validate witness information when required"""
        for record in self:
            if (
                record.state == "issued"
                and record.witness_required
                and not record.witness_name
            ):
                raise ValidationError(
                    _("Witness information is required for issued certificates")
                

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Update customer contact when partner changes"""
        if self.partner_id:
            contacts = self.partner_id.child_ids.filtered(
                lambda c: c.is_company == False
            
            if contacts:
                self.customer_contact_id = contacts[0]
            else:
                pass
            pass
            pass
                self.customer_contact_id = False

    @api.onchange("destruction_method")
    def _onchange_destruction_method(self):
        """Update certification statement based on method"""
        if self.destruction_method:
            method_statements = {
                "cross_cut": "Documents were destroyed using cross-cut shredding in accordance with NAID Level AAA standards.",
                "pulverization": "Materials were destroyed through pulverization to particles no larger than 5mm.",
                "incineration": "Documents were completely incinerated at temperatures exceeding 1800°F.",
                "degaussing": "Electronic media was degaussed using NAID-approved equipment.",
            }

            base_statement = method_statements.get(self.destruction_method, "")
            if base_statement:
                full_statement = f"{base_statement} This destruction was witnessed and verified according to established chain of custody procedures."
                self.certification_statement = full_statement

    @api.onchange("shredding_service_ids")
    def _onchange_services(self):
        """Update certificate totals when services change"""
        if self.shredding_service_ids:
            self._update_totals_from_services()
