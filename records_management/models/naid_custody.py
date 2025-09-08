# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class NaidCustody(models.Model):
    """
    Represents a single event in the chain of custody for a document,
    adhering to NAID AAA certification requirements. Each record tracks
    who handled a document, when, and for what purpose.
    """
    _name = 'naid.custody'
    _description = 'NAID Chain of Custody Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc, id desc'
    # Use explicit name field for view compatibility (form title uses <field name="name"/>)
    _rec_name = 'name'

    name = fields.Char(
        string="Reference",
        required=False,
        index=True,
        copy=False,
        help="Short reference for this custody event (auto-generated if left blank)."
    )
    document_id = fields.Many2one(
        'records.document',
        string="Document",
        required=True,
        ondelete='cascade',
        help="The document this custody event belongs to."
    )
    event_date = fields.Datetime(
        string="Event Date",
        default=fields.Datetime.now,
        required=True,
        help="Timestamp of the custody event."
    )
    user_id = fields.Many2one(
        'res.users',
        string="Custody Owner",  # Disambiguated from activity_user_id label 'Responsible User'
        default=lambda self: self.env.user,
        required=True,
        help="The user responsible for this custody event."
    )
    description = fields.Text(
        string="Event Description",
        required=True,
        help="Detailed description of the event (e.g., 'Picked up from customer', 'Entered storage')."
    )
    location_id = fields.Many2one(
        'stock.location',
        string="Location",
        help="The physical or logical location associated with this event."
    )
    partner_id = fields.Many2one(
        related='document_id.partner_id',
        string="Customer",
        store=True,
        readonly=True,
        comodel_name='res.partner',
        help="The customer associated with the document."
    )
    event_type = fields.Selection([
        ('creation', 'Creation'),
        ('pickup', 'Pickup'),
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('transfer', 'Transfer'),
        ('destruction', 'Destruction'),
        ('audit', 'Audit'),
        ('other', 'Other')
    ], string="Event Type", default='creation', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-generate reference if not provided
            if not vals.get('name'):
                # Build a lightweight reference using event_type and datetime once record exists
                # Placeholder; will refine after create in write-back if needed
                vals['name'] = _('Custody Event')
        records = super().create(vals_list)
        for rec in records:
            # Post-creation enhancement including date and event type for uniqueness
            if rec.name == _('Custody Event'):
                rec.name = f"{rec.event_type.upper()}-{rec.id}"
        return records

    def name_get(self):
        result = []
        for record in self:
            base = record.name or record.description or _('Custody Event')
            name = f"{base} - {record.event_type}" if record.event_type else base
            result.append((record.id, name))
        return result
