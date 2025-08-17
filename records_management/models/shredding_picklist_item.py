from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ShreddingPicklistItem(models.Model):
    _name = 'shredding.picklist.item'
    _description = 'Shredding Picklist Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'picklist_id, sequence, container_id'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    picklist_id = fields.Many2one()
    batch_id = fields.Many2one()
    container_id = fields.Many2one()
    partner_id = fields.Many2one()
    location_id = fields.Many2one()
    container_type = fields.Selection()
    container_barcode = fields.Char()
    container_volume_cf = fields.Float()
    quantity = fields.Float()
    weight_kg = fields.Float()
    weight_lbs = fields.Float()
    estimated_shred_time = fields.Float()
    status = fields.Selection()
    collection_date = fields.Datetime()
    shred_start_time = fields.Datetime()
    shred_completion_time = fields.Datetime()
    certification_date = fields.Datetime()
    collected_by = fields.Many2one()
    shredded_by = fields.Many2one()
    witness_employee_id = fields.Many2one()
    shredding_equipment_id = fields.Many2one()
    shred_method = fields.Selection()
    security_level = fields.Selection()
    destruction_certificate_id = fields.Many2one()
    naid_compliant = fields.Boolean()
    audit_trail_ids = fields.One2many()
    chain_of_custody_id = fields.Many2one()
    exception_reason = fields.Text()
    resolution_notes = fields.Text()
    exception_resolved = fields.Boolean()
    collection_notes = fields.Text()
    shredding_notes = fields.Text()
    quality_notes = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    collection_date = fields.Datetime()
    shred_start_time = fields.Datetime()
    shred_completion_time = fields.Datetime()
    certification_date = fields.Datetime()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with container info"""
            for item in self:
                parts = []
                if item.container_id:
                    parts.append(item.container_id.name or item.container_barcode)
                if item.name:
                    parts.append(item.name)
                else:
                    parts.append(_("Shred Item"))

                item.display_name = " - ".join(parts) if parts else _("New Item"):

    def _compute_weight_lbs(self):
            """Convert weight from kg to lbs"""
            for item in self:
                if item.weight_kg:
                    item.weight_lbs = item.weight_kg * 2.20462  # kg to lbs conversion
                else:
                    item.weight_lbs = 0.0

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_container_id(self):
            """Update fields when container changes"""
            if self.container_id:
                # Auto-populate container-related fields
                if not self.name:
                    self.name = _("Shred: %s", self.container_id.name or self.container_id.barcode)

                # Set estimated weight if available:
                if self.container_id.weight_pounds and not self.weight_kg:
                    self.weight_kg = self.container_id.weight_pounds * 0.453592  # lbs to kg

                # Set security level based on container
                if hasattr(self.container_id, 'security_level'):
                    self.security_level = self.container_id.security_level


    def _onchange_status(self):
            """Update timestamps when status changes"""
            if self.status == 'collected' and not self.collection_date:

    def action_collect_item(self):
            """Mark item as collected"""
            self.ensure_one()
            if self.status != 'pending':
                raise UserError(_("Can only collect pending items"))

            self.write({)}
                'status': 'collected',
                'collection_date': fields.Datetime.now(),
                'collected_by': self.env.user.employee_id.id if self.env.user.employee_id else False:


            self._create_audit_log('item_collected')
            self.message_post(body=_("Item collected for shredding")):

    def action_start_shredding(self):
            """Start the shredding process"""
            self.ensure_one()
            if self.status not in ['collected', 'in_queue']:
                raise UserError(_("Can only start shredding collected or queued items"))

            self.write({)}
                'status': 'shredding',
                'shred_start_time': fields.Datetime.now(),
                'shredded_by': self.env.user.employee_id.id if self.env.user.employee_id else False:


            self._create_audit_log('shredding_started')
            self.message_post(body=_("Shredding process started"))


    def action_complete_shredding(self):
            """Complete the shredding process"""
            self.ensure_one()
            if self.status != 'shredding':
                raise UserError(_("Can only complete items currently being shredded"))

            # Validate required information
            if not self.shredding_equipment_id:
                raise UserError(_("Please specify the shredding equipment used"))

            if not self.shred_method:
                raise UserError(_("Please specify the shredding method"))

            self.write({)}
                'status': 'shredded',
                'shred_completion_time': fields.Datetime.now()


            self._create_audit_log('shredding_completed')
            self._update_container_status()
            self.message_post(body=_("Shredding completed successfully"))


    def action_certify_destruction(self):
            """Certify the destruction and generate certificate"""
            self.ensure_one()
            if self.status != 'shredded':
                raise UserError(_("Can only certify shredded items"))

            # Generate destruction certificate if not exists:
            if not self.destruction_certificate_id:
                self._generate_destruction_certificate()

            self.write({)}
                'status': 'certified',
                'certification_date': fields.Datetime.now()


            self._create_audit_log('destruction_certified')
            self.message_post(body=_("Destruction certified"))


    def action_mark_exception(self):
            """Mark item as exception"""
            self.ensure_one()
            if not self.exception_reason:
                raise UserError(_("Please provide an exception reason"))

            self.write({'status': 'exception'})
            self._create_audit_log('exception_marked')
            self.message_post(body=_("Item marked as exception: %s", self.exception_reason))


    def action_resolve_exception(self):
            """Resolve exception and continue process"""
            self.ensure_one()
            if self.status != 'exception':
                raise UserError(_("Can only resolve items with exception status"))

            if not self.resolution_notes:
                raise UserError(_("Please provide resolution notes"))

            self.write({)}
                'status': 'collected',  # Return to collected status
                'exception_resolved': True


            self._create_audit_log('exception_resolved')
            self.message_post(body=_("Exception resolved: %s", self.resolution_notes))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_quantity(self):
            """Validate quantity is positive"""
            for item in self:
                if item.quantity <= 0:
                    raise ValidationError(_("Quantity must be greater than 0"))


    def _check_weight(self):
            """Validate weight values"""
            for item in self:
                if item.weight_kg < 0:
                    raise ValidationError(_("Weight cannot be negative"))
                if item.weight_kg > 1000:  # Reasonable upper limit
                    raise ValidationError(_("Weight seems unrealistic. Please verify."))


    def _check_shred_times(self):
            """Validate shredding time sequence"""
            for item in self:
                if (item.shred_start_time and item.shred_completion_time and:)
                    item.shred_start_time > item.shred_completion_time
                    raise ValidationError(_("Shred start time must be before completion time"))


    def _check_collection_shred_sequence(self):
            """Validate collection happens before shredding"""
            for item in self:
                if (item.collection_date and item.shred_start_time and:)
                    item.collection_date > item.shred_start_time
                    raise ValidationError(_("Collection must happen before shredding"))

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def _create_audit_log(self, action_type):
            """Create NAID compliance audit log entry"""
            self.ensure_one()

            audit_vals = {}
                'action_type': action_type,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'container_id': self.container_id.id,
                'shred_item_id': self.id,
                'description': _("Shred item %s: %s", self.display_name, action_type),
                'naid_compliant': self.naid_compliant,


            return self.env['naid.audit.log'].create(audit_vals)


    def _update_container_status(self):
            """Update container status after shredding"""
            self.ensure_one()
            if self.container_id:
                self.container_id.write({)}
                    'status': 'destroyed',
                    'destruction_date': fields.Date.today()



    def _generate_destruction_certificate(self):
            """Generate destruction certificate for this item""":
            self.ensure_one()

            certificate_vals = {}
                'name': _("Certificate - %s", self.display_name),
                'container_ids': [(6, 0, [self.container_id.id])],
                'destruction_date': fields.Date.today(),
                'destruction_method': self.shred_method,
                'equipment_id': self.shredding_equipment_id.id if self.shredding_equipment_id else False,:
                'witness_id': self.witness_employee_id.id if self.witness_employee_id else False,:
                'naid_compliant': self.naid_compliant,


            certificate = self.env['naid.certificate'].create(certificate_vals)
            self.destruction_certificate_id = certificate.id
            return certificate


    def get_process_duration(self):
            """Calculate processing duration metrics"""
            self.ensure_one()

            durations = {}

            if self.collection_date and self.shred_start_time:
                delta = self.shred_start_time - self.collection_date
                durations['queue_time'] = delta.total_seconds() / 3600  # hours

            if self.shred_start_time and self.shred_completion_time:
                delta = self.shred_completion_time - self.shred_start_time
                durations['shred_time'] = delta.total_seconds() / 60  # minutes

            if self.collection_date and self.certification_date:
                delta = self.certification_date - self.collection_date
                durations['total_time'] = delta.total_seconds() / 3600  # hours

            return durations

        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def get_shredding_statistics(self, date_from=None, date_to=None):
            """Get shredding statistics for reporting""":
            domain = []
            if date_from:
                domain.append(('collection_date', '>=', date_from))
            if date_to:
                domain.append(('collection_date', '<=', date_to))

            items = self.search(domain)

            stats = {}
                'total_items': len(items),
                'total_weight_kg': sum(items.mapped('weight_kg')),
                'by_status': {},
                'by_container_type': {},
                'by_security_level': {},


            # Status distribution
            for status in ['pending', 'collected', 'shredded', 'certified', 'exception']:
                status_items = items.filtered(lambda i: i.status == status)
                stats['by_status'][status] = {}
                    'count': len(status_items),
                    'weight_kg': sum(status_items.mapped('weight_kg'))


            # Container type distribution
            for item in items:
                container_type = item.container_type or 'unknown'
                if container_type not in stats['by_container_type']:
                    stats['by_container_type'][container_type] = {}
                        'count': 0,
                        'weight_kg': 0.0

                stats['by_container_type'][container_type]['count'] += 1
                stats['by_container_type'][container_type]['weight_kg'] += item.weight_kg or 0

            # Security level distribution
            for item in items:
                security_level = item.security_level or 'standard'
                if security_level not in stats['by_security_level']:
                    stats['by_security_level'][security_level] = {}
                        'count': 0,
                        'weight_kg': 0.0

                stats['by_security_level'][security_level]['count'] += 1
                stats['by_security_level'][security_level]['weight_kg'] += item.weight_kg or 0

            return stats

        # ============================================================================
            # ORM METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create to set defaults and create audit logs"""
            for vals in vals_list:
                if not vals.get('name'):
                    vals['name'] = _("Shred Item %s", fields.Datetime.now().strftime('%Y%m%d-%H%M%S'))

            items = super().create(vals_list)

            for item in items:
                item._create_audit_log('item_created')

            return items


    def write(self, vals):
            """Override write to track status changes"""
            result = super().write(vals)

            if 'status' in vals:
                for item in self:
                    status_label = dict(item._fields['status'].selection)[item.status]
                    item.message_post(body=_("Status changed to %s", status_label))

            return result


    def name_get(self):
            """Custom name display"""
            result = []
            for item in self:
                name = item.display_name or item.name
                if item.status != 'pending':
                    status_label = dict(item._fields['status'].selection)[item.status]
                    name = _("%s [%s]", name, status_label)
                result.append((item.id, name))
            return result

        # ============================================================================
            # INTEGRATION METHODS
        # ============================================================================

    def action_view_container(self):
            """View the related container"""
            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Container Details'),
                'res_model': 'records.container',
                'res_id': self.container_id.id,
                'view_mode': 'form',
                'target': 'current',



    def action_view_destruction_certificate(self):
            """View destruction certificate"""
            self.ensure_one()
            if not self.destruction_certificate_id:
                raise UserError(_("No destruction certificate available"))

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Destruction Certificate'),
                'res_model': 'naid.certificate',
                'res_id': self.destruction_certificate_id.id,
                'view_mode': 'form',
                'target': 'current',



    def action_print_label(self):
            """Print item label for tracking""":
            self.ensure_one()
            return self.env.ref('records_management.shred_item_label_report').report_action(self)

