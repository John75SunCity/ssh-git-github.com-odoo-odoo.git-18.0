from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class CustodyTransferEvent(models.Model):
    _name = 'custody.transfer.event'
    _description = 'Custody Transfer Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transfer_date desc, transfer_time desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    custody_record_id = fields.Many2one()
    work_order_id = fields.Many2one()
    transfer_date = fields.Date()
    transfer_time = fields.Datetime()
    transfer_type = fields.Selection()
    transferred_from_id = fields.Many2one()
    transferred_to_id = fields.Many2one()
    witness_id = fields.Many2one()
    from_location = fields.Char()
    to_location = fields.Char()
    gps_latitude = fields.Float()
    gps_longitude = fields.Float()
    items_description = fields.Text()
    item_count = fields.Integer()
    total_weight = fields.Float()
    total_volume = fields.Float()
    container_numbers = fields.Text()
    verification_method = fields.Selection()
    security_seal_number = fields.Char()
    transfer_authorized = fields.Boolean()
    authorization_code = fields.Char()
    transfer_document = fields.Binary()
    transfer_document_filename = fields.Char()
    photos_taken = fields.Boolean()
    notes = fields.Text()
    transferred_from_signature = fields.Binary()
    transferred_to_signature = fields.Binary()
    witness_signature = fields.Binary()
    status = fields.Selection()
    naid_compliant = fields.Boolean()
    compliance_issues = fields.Text()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_naid_compliant(self):
            """Check NAID compliance requirements"""
            for record in self:
                record.naid_compliant = bool()
                    record.transferred_from_signature and
                    record.transferred_to_signature and
                    record.transfer_authorized and
                    record.verification_method


        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_start_transfer(self):
            """Start the custody transfer"""
            self.ensure_one()
            if self.status != 'pending':
                raise UserError(_('Can only start pending transfers'))

            self.write({'status': 'in_progress'})
            self.message_post(body=_('Custody transfer started'))


    def action_complete_transfer(self):
            """Complete the custody transfer"""
            self.ensure_one()
            if self.status != 'in_progress':
                raise UserError(_('Can only complete transfers in progress'))

            # Validate required signatures
            if not self.transferred_from_signature or not self.transferred_to_signature:
                raise UserError(_('Both transferor and receiver signatures are required'))

            self.write({)}
                'status': 'completed',
                'transfer_time': fields.Datetime.now()

            self.message_post(body=_('Custody transfer completed'))


    def action_verify_transfer(self):
            """Verify the custody transfer"""
            self.ensure_one()
            if self.status != 'completed':
                raise UserError(_('Can only verify completed transfers'))

            self.write({'status': 'verified'})
            self.message_post(body=_('Custody transfer verified'))


    def action_dispute_transfer(self):
            """Mark transfer as disputed"""
            self.ensure_one()
            if self.status in ('cancelled', 'disputed'):
                raise UserError(_('Cannot dispute cancelled or already disputed transfers'))

            self.write({'status': 'disputed'})
            self.message_post(body=_('Custody transfer disputed'))


    def action_cancel_transfer(self):
            """Cancel the custody transfer"""
            self.ensure_one()
            if self.status in ('completed', 'verified', 'cancelled'):
                raise UserError(_('Cannot cancel completed, verified, or already cancelled transfers'))

            self.write({'status': 'cancelled'})
            self.message_post(body=_('Custody transfer cancelled'))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_gps_coordinates(self):
            """Validate GPS coordinates"""
            for record in self:
                if record.gps_latitude and not (-90 <= record.gps_latitude <= 90):
                    raise ValidationError(_('GPS latitude must be between -90 and 90 degrees'))
                if record.gps_longitude and not (-180 <= record.gps_longitude <= 180):
                    raise ValidationError(_('GPS longitude must be between -180 and 180 degrees'))


    def _check_quantities(self):
            """Validate quantities are positive"""
            for record in self:
                if record.item_count and record.item_count < 0:
                    raise ValidationError(_('Item count cannot be negative'))
                if record.total_weight and record.total_weight < 0:
                    raise ValidationError(_('Total weight cannot be negative'))
                if record.total_volume and record.total_volume < 0:
                    raise ValidationError(_('Total volume cannot be negative'))
