# -*- coding: utf-8 -*-
"""
Account Move Extensions for Automatic Certificate of Destruction Generation

Extends account.move model to automatically generate certificates of destruction
for shredding/destruction-related invoice lines when invoices are confirmed.

Author: Records Management System
Version: 18.0.0.1
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """
    Account Move Extensions for Records Management

    Extends the standard account.move model to provide automatic certificate
    of destruction generation for shredding and destruction services when
    invoices are confirmed/posted.
    """

    _inherit = "account.move"

    # ============================================================================
    # DESTRUCTION CERTIFICATE TRACKING
    # ============================================================================
    destruction_certificate_ids = fields.One2many(
        'destruction.certificate',
        'invoice_id',
        string='Destruction Certificates',
        help='Certificates of destruction generated from this invoice'
    )

    destruction_certificate_count = fields.Integer(
        string='Certificate Count',
        compute='_compute_destruction_certificate_count',
        help='Number of destruction certificates linked to this invoice'
    )

    has_destruction_services = fields.Boolean(
        string='Has Destruction Services',
        compute='_compute_has_destruction_services',
        store=True,
        help='Indicates if this invoice contains destruction/shredding services'
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('destruction_certificate_ids')
    def _compute_destruction_certificate_count(self):
        """Compute number of destruction certificates"""
        for move in self:
            move.destruction_certificate_count = len(move.destruction_certificate_ids)

    @api.depends('invoice_line_ids', 'invoice_line_ids.records_service_type')
    def _compute_has_destruction_services(self):
        """Check if invoice has destruction/shredding services"""
        for move in self:
            move.has_destruction_services = any(
                line.records_service_type == 'destruction' 
                for line in move.invoice_line_ids
            )

    # ============================================================================
    # CERTIFICATE GENERATION METHODS
    # ============================================================================
    def _generate_destruction_certificates(self):
        """
        Generate certificates of destruction for all destruction-related invoice lines.
        
        This method is called automatically when an invoice is posted/confirmed.
        Creates one certificate per destruction service line that doesn't already have one.
        """
        self.ensure_one()

        if self.move_type not in ['out_invoice', 'out_refund']:
            return

        destruction_lines = self.invoice_line_ids.filtered(
            lambda line: line.records_service_type == 'destruction' 
            and not line.certificate_of_destruction_id
        )

        if not destruction_lines:
            return

        Certificate = self.env['destruction.certificate']
        certificates_created = []

        for line in destruction_lines:
            # Prepare certificate values
            cert_vals = {
                'name': _('Certificate - %s - %s') % (self.name, line.name or line.product_id.name),
                'partner_id': self.partner_id.id,
                'invoice_id': self.id,
                'invoice_line_id': line.id,
                'certificate_date': fields.Date.today(),
                'destruction_date': line.pickup_date or self.invoice_date or fields.Date.today(),
                'destruction_method': line.destruction_method or 'cross_cut',
                'total_weight': line.shredding_weight_lbs or 0.0,
                'container_count': line.container_count or 0,
                'state': 'draft',
                'notes': _('Certificate generated automatically from invoice %s') % self.name,
            }

            # Add department if available
            if line.records_department_id:
                cert_vals['department_id'] = line.records_department_id.id

            # Add containers if available
            if line.container_ids:
                cert_vals['container_ids'] = [(6, 0, line.container_ids.ids)]

            # Add destruction service reference if available
            if line.destruction_service_id:
                cert_vals['destruction_service_id'] = line.destruction_service_id.id

            # Add location information
            if line.origin_location_id:
                cert_vals['location_id'] = line.origin_location_id.id
            elif line.storage_location_id:
                cert_vals['location_id'] = line.storage_location_id.id

            # Create the certificate
            certificate = Certificate.create(cert_vals)
            
            # Link certificate back to invoice line
            line.certificate_of_destruction_id = certificate.id

            certificates_created.append(certificate)

            # Post message on invoice line
            line.message_post(
                body=_('Certificate of Destruction %s generated automatically') % certificate.name
            )

        # Post message on invoice if certificates were created
        if certificates_created:
            cert_names = ', '.join(cert.name for cert in certificates_created)
            self.message_post(
                body=_('Generated %s Certificate(s) of Destruction: %s') % (
                    len(certificates_created), 
                    cert_names
                )
            )

        return certificates_created

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_destruction_certificates(self):
        """View destruction certificates for this invoice"""
        self.ensure_one()

        if not self.destruction_certificate_ids:
            raise UserError(_('No destruction certificates found for this invoice.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Destruction Certificates'),
            'res_model': 'destruction.certificate',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.destruction_certificate_ids.ids)],
            'context': {'default_invoice_id': self.id},
        }

    def action_generate_destruction_certificates(self):
        """Manual action to generate destruction certificates"""
        self.ensure_one()

        if self.state != 'posted':
            raise UserError(_('Certificates can only be generated for posted invoices.'))

        certificates = self._generate_destruction_certificates()

        if not certificates:
            raise UserError(_('No destruction services found on this invoice, or certificates already exist.'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Generated %s certificate(s) of destruction.') % len(certificates),
                'type': 'success',
                'sticky': False,
            }
        }

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    def action_post(self):
        """Override to automatically generate destruction certificates when posting"""
        res = super(AccountMove, self).action_post()

        # Generate certificates for newly posted invoices with destruction services
        for move in self:
            if move.has_destruction_services and move.state == 'posted':
                try:
                    move._generate_destruction_certificates()
                except Exception as e:
                    # Log error but don't block invoice posting
                    move.message_post(
                        body=_('Warning: Failed to auto-generate destruction certificates: %s') % str(e)
                    )

        return res

    def button_draft(self):
        """Override to handle certificate state when setting invoice to draft"""
        res = super(AccountMove, self).button_draft()

        # Optionally cancel/draft related certificates
        for move in self:
            if move.destruction_certificate_ids:
                draft_certs = move.destruction_certificate_ids.filtered(lambda c: c.state == 'draft')
                # Could optionally unlink draft certificates or set them to cancelled
                # For now, just log a message
                if draft_certs:
                    move.message_post(
                        body=_('Invoice reset to draft. Please review linked destruction certificates.')
                    )

        return res
