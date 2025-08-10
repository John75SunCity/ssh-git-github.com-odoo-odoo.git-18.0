# -*- coding: utf-8 -*-
"""
Records Container Type Converter Module

This module provides comprehensive container type conversion functionality for the Records Management System.
It enables bulk conversion of container types with validation, tracking, and audit trails to support
operational flexibility and compliance requirements.

Key Features:
- Bulk container type conversion with validation
- Conversion preview and impact analysis
- Complete audit trail and change tracking
- Integration with container lifecycle management
- Support for business rule validation
- Automated conversion reporting and notifications

Business Processes:
1. Container Selection: Choose containers for type conversion
2. Type Validation: Validate source and target container types
3. Impact Analysis: Preview conversion changes and potential impacts
4. Conversion Execution: Perform bulk type conversion with validation
5. Audit Tracking: Complete audit trail of all conversion activities
6. Notification: Automated notifications for conversion completion

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerTypeConverter(models.Model):
    _name = "records.container.type.converter"
    _description = "Records Container Type Converter"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "created_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Converter Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for the conversion process",
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    
    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for the conversion",
    
    active = fields.Boolean(
        string="Active", default=True, help="Active status of the converter"
    

    # ============================================================================
    # CONVERSION CONFIGURATION
    # ============================================================================
    source_type = fields.Char(
        string="Source Type",
        required=True,
        tracking=True,
        help="Original container type to convert from",
    
    target_type = fields.Char(
        string="Target Type",
        required=True,
        tracking=True,
        help="New container type to convert to",
    
    current_type = fields.Char(
        string="Current Container Type",
        help="Current type of containers being processed",
    
    new_container_type_code = fields.Char(
        string="New Container Type Code", help="Code for the new container type"
    
    target_container_type = fields.Char(
        string="Target Container Type",
        help="Alternative reference for target container type",
    

    # ============================================================================
    # CONTAINER SELECTION AND MANAGEMENT
    # ============================================================================
    container_ids = fields.One2many(
        "records.container",
        "converter_id",
        string="Containers to Convert",
        help="List of containers selected for type conversion",
    
    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_metrics",
        store=True,
        help="Total number of containers to convert",
    
    eligible_containers = fields.Integer(
        string="Eligible Containers",
        compute="_compute_container_metrics",
        store=True,
        help="Number of containers eligible for conversion",
    
    blocked_containers = fields.Integer(
        string="Blocked Containers",
        compute="_compute_container_metrics",
        store=True,
        help="Number of containers that cannot be converted",
    

    # ============================================================================
    # BUSINESS CONTEXT FIELDS
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        tracking=True,
        help="Customer associated with the containers",
    
    location_id = fields.Many2one(
        "records.location",
        string="Location",
        tracking=True,
        help="Physical location of the containers",
    
    container_type = fields.Selection(
        selection="_get_container_type_selection",
        string="Container Type",
        help="Container type selection",
    

    # ============================================================================
    # CONVERSION DETAILS AND TRACKING
    # ============================================================================
    reason = fields.Text(
        string="Conversion Reason",
        required=True,
        help="Business justification for the conversion",
    
    conversion_notes = fields.Text(
        string="Conversion Notes", help="Additional notes about the conversion process"
    
    summary_line = fields.Char(
        string="Summary Line",
        compute="_compute_summary_line",
        store=True,
        help="Summary of the conversion operation",
    

    # ============================================================================
    # STATUS AND WORKFLOW MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the conversion process",
    

    # ============================================================================
    # CONTAINER PROPERTIES
    # ============================================================================
    barcode = fields.Char(string="Barcode", copy=False, help="Barcode identifier")
    capacity = fields.Float(
        string="Capacity", digits=(10, 2), help="Container capacity"
    
    current_weight = fields.Float(
        string="Current Weight", digits=(10, 2), help="Current weight of the container"
    
    last_access_date = fields.Date(
        string="Last Access Date", help="Date of last container access"
    

    # ============================================================================
    # ADMINISTRATIVE FIELDS
    # ============================================================================
    sequence = fields.Integer(
        string="Sequence", default=10, help="Sequence for ordering converters"
    
    notes = fields.Text(string="Notes", help="General notes about the converter")
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
        help="Date when the converter was created",
    
    updated_date = fields.Datetime(
        string="Updated Date", help="Date when the converter was last updated"
    

    # ============================================================================
    # CONVERSION RESULTS AND METRICS
    # ============================================================================
    conversion_date = fields.Datetime(
        string="Conversion Date", help="Date when the conversion was completed"
    
    converted_count = fields.Integer(
        string="Converted Count",
        default=0,
        help="Number of containers successfully converted",
    
    failed_count = fields.Integer(
        string="Failed Count",
        default=0,
        help="Number of containers that failed conversion",
    
    success_rate = fields.Float(
        string="Success Rate (%)",
        compute="_compute_success_rate",
        store=True,
        help="Percentage of successful conversions",
    

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[("res_model", "=", "records.container.type.converter")],
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[("res_model", "=", "records.container.type.converter")],
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=[("res_model", "=", "records.container.type.converter")],
    

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("source_type", "target_type", "container_ids")
    def _compute_summary_line(self):
        """Compute summary line for conversion"""
        for record in self:
            container_count = len(record.container_ids)
            source = record.source_type or "Unknown"
            target = record.target_type or "Unknown"
            record.summary_line = (
                f"Convert {container_count} containers from {source} to {target}"
            

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", 
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    

    @api.depends("container_ids")
    def _compute_container_metrics(self):
        """Compute container metrics for conversion planning"""
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)

            # Count eligible containers (not destroyed, archived, or permanent)
            eligible = containers.filtered(
                lambda c: c.state not in ["destroyed", "archived"]
                and not getattr(c, "is_permanent", False)
            
            record.eligible_containers = len(eligible)
            record.blocked_containers = (
                record.container_count - record.eligible_containers
            

    @api.depends("converted_count", "container_count")
    def _compute_success_rate(self):
        """Calculate conversion success rate"""
        for record in self:
            if record.container_count > 0:
                record.success_rate = (
                    record.converted_count / record.container_count
                ) * 100
            else:
                pass
            pass
                record.success_rate = 0.0

    # ============================================================================
    # VALIDATION CONSTRAINTS
    # ============================================================================
    @api.constrains("source_type", "target_type")
    def _check_conversion_types(self):
        """Validate that source and target types are different and valid"""
        for record in self:
            if record.source_type and record.target_type:
                pass
                if record.source_type == record.target_type:
                    raise ValidationError(
                        _("Source type and target type cannot be the same.")
                    

    @api.constrains("container_ids")
    def _check_container_eligibility(self):
        """Validate that selected containers can be converted"""
        for record in self:
            if record.container_ids:
                blocked = record.container_ids.filtered(
                    lambda c: c.state in ["destroyed", "archived"]
                    or getattr(c, "is_permanent", False)
                
                if blocked:
                    raise ValidationError(
                        _("Some selected containers cannot be converted: %s", "), ".join(blocked.mapped("name"))
                    

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and defaults"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "records.container.type.converter"
                    
                    or "CONV-NEW"
                
            vals["updated_date"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to update timestamp"""
        vals["updated_date"] = fields.Datetime.now()
        return super().write(vals)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def _get_container_type_selection(self):
        """Get available container types for selection"""
        try:
            container_types = self.env["records.container.type"].search([])
            return [(ct.code, ct.name) for ct in container_types]
        except Exception as e:
            # Log the exception for debugging
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error("Error fetching container types: %s", e)
            # Fallback selection if model doesn't exist
            return [
                ("TYPE_01", "File Storage Box"),
                ("TYPE_02", "Document Archive Box"),
                ("TYPE_03", "Media Storage Container"),
                ("TYPE_04", "Secure Document Box"),
                ("TYPE_05", "Temporary Storage Box"),
            ]

    def get_eligible_containers(self):
        """Get containers eligible for conversion"""
        self.ensure_one()
        return self.container_ids.filtered(
            lambda c: c.state not in ["destroyed", "archived"]
            and not getattr(c, "is_permanent", False)
        

    def get_blocked_containers(self):
        """Get containers that cannot be converted"""
        self.ensure_one()
        return self.container_ids.filtered(
            lambda c: c.state in ["destroyed", "archived"]
            or getattr(c, "is_permanent", False)
        

    def validate_conversion(self):
        """Validate that conversion can proceed"""
        self.ensure_one()

        if not self.container_ids:
            raise UserError(_("No containers selected for conversion."))

        if not self.target_type:
            raise UserError(_("Target container type must be specified."))

        blocked_containers = self.get_blocked_containers()
        if blocked_containers:
            raise UserError(
                _(
                    "Cannot convert containers that are destroyed, archived, or permanent: %s"
                
                % ", ".join(blocked_containers.mapped("name"))
            

        return True

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_validate_conversion(self):
        """Validate the conversion setup"""
        self.ensure_one()

        try:
            self.validate_conversion()
            self.write({"state": "validated"})
            self.message_post(body=_("Action completed"))body=_("Conversion validated successfully"))

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Validation Successful"),
                    "message": _("Conversion setup is valid and ready to proceed."),
                    "type": "success",
                    "sticky": False,
                },
            }
        except UserError as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Validation Failed"),
                    "message": str(e),
                    "type": "danger",
                    "sticky": True,
                },
            }

    def action_preview_conversion(self):
        """Preview conversion results with validation"""
        self.ensure_one()

        if not self.container_ids:
            raise UserError(_("No containers selected to preview."))

        eligible_containers = self.get_eligible_containers()
        blocked_containers = self.get_blocked_containers()

        # Warn user if there are blocked containers
        if blocked_containers:
            # Could add a warning message or modify context based on blocked containers
            pass

        # Create preview context with container information
        context = {
            "default_converter_id": self.id,
            "search_default_group_by_type": 1,
            "eligible_count": len(eligible_containers),
            "blocked_count": len(blocked_containers),
        }

        return {
            "type": "ir.actions.act_window",
            "name": _("Conversion Preview: %s", self.name),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.container_ids.ids)],
            "context": context,
            "target": "new",
        }

    def action_convert_containers(self):
        """Convert containers with proper validation and tracking"""
        self.ensure_one()

        # Validate conversion can proceed
        self.validate_conversion()

        # Update state to in progress
        self.write(
            {
                "state": "in_progress",
                "conversion_date": fields.Datetime.now(),
            }
        

        eligible_containers = self.get_eligible_containers()
        converted_count = 0
        failed_count = 0

        # Process each eligible container
        for container in eligible_containers:
            try:
                # Prepare update values
                update_vals = {
                    "container_type": self.target_type,
                }

                # Add conversion tracking fields if they exist
                container_fields = container._fields
                if "conversion_date" in container_fields:
                    update_vals["conversion_date"] = fields.Datetime.now()
                if "conversion_reason" in container_fields:
                    update_vals["conversion_reason"] = self.reason or "Bulk conversion"
                if "previous_type" in container_fields:
                    update_vals["previous_type"] = container.container_type

                # Add conversion note to container notes
                if "notes" in container_fields and self.reason:
                    current_notes = container.notes or ""
                    conversion_note = (
                        f"\n[{fields.Datetime.now()}] "
                        f"Converted from {self.source_type} to {self.target_type}: {self.reason}"
                    
                    update_vals["notes"] = current_notes + conversion_note

                # Perform the conversion
                container.write(update_vals)
                converted_count += 1

            except Exception as e:
                # Log conversion failure
                self.message_post(body=_("Action completed"))
                    body=_("Failed to convert container %s: %s", (container.name), str(e))
                
                failed_count += 1

        # Update conversion results
        self.write(
            {
                "state": "completed",
                "converted_count": converted_count,
                "failed_count": failed_count,
            }
        

        # Log the conversion activity
        self.message_post(body=_("Action completed"))
            body=_(
                "Conversion completed: %d containers converted from %s to %s (%d failed)"
            
            % (converted_count, self.source_type, self.target_type, failed_count)
        

        # Return success notification
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Conversion Completed"),
                "message": _("Successfully converted %d containers (%d failed).", (converted_count), failed_count),
                "type": "success" if failed_count == 0 else "warning",
                "sticky": False,
            },
        }

    def action_cancel_conversion(self):
        """Cancel the conversion process"""
        self.ensure_one()

        if self.state == "completed":
            raise UserError(_("Cannot cancel a completed conversion."))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Action completed"))body=_("Conversion cancelled"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Conversion Cancelled"),
                "message": _("Conversion process has been cancelled."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_reset_to_draft(self):
        """Reset conversion to draft state"""
        self.ensure_one()

        if self.state == "completed":
            raise UserError(_("Cannot reset a completed conversion."))

        self.write(
            {
                "state": "draft",
                "converted_count": 0,
                "failed_count": 0,
                "conversion_date": False,
            }
        
        self.message_post(body=_("Action completed"))body=_("Conversion reset to draft"))

        return True

    def action_view_containers(self):
        """View containers associated with this converter"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Containers: %s", self.name),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.container_ids.ids)],
            "context": {"default_converter_id": self.id},
        }

    def action_generate_conversion_report(self):
        """Generate conversion report"""
        self.ensure_one()

        return self.env.ref(
            "records_management.action_report_container_conversion"
        ).report_action(self)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = [record.name]

            if record.source_type and record.target_type:
                name_parts.append(f"({record.source_type} → {record.target_type})")

            if record.container_count:
                name_parts.append(f"[{record.container_count} containers]")

            result.append((record.id, " ".join(name_parts)))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, source type, or target type"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("source_type", operator, name),
                ("target_type", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def get_conversion_summary(self):
        """Get conversion summary for reporting"""
        self.ensure_one()
        return {
            "converter_name": self.name,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "total_containers": self.container_count,
            "eligible_containers": self.eligible_containers,
            "blocked_containers": self.blocked_containers,
            "converted_count": self.converted_count,
            "failed_count": self.failed_count,
            "success_rate": self.success_rate,
            "conversion_date": self.conversion_date,
            "reason": self.reason,
            "status": self.state,
        }
