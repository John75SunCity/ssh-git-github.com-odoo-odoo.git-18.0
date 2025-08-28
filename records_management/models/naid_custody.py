# -*- coding: utf-8 -*-

from odoo import models, fields, api

class NaidCustody(models.Model):
    """
    Represents a single event in the chain of custody for a document,
    adhering to NAID AAA certification requirements. Each record tracks
    who handled a document, when, and for what purpose.
    """
    _name = 'naid.custody'
    _description = 'NAID Chain of Custody Log'
    _order = 'event_date desc, id desc'
    _rec_name = 'description'

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
        string="Responsible User",
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

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.event_date}] {record.event_type} - {record.user_id.name}"
            result.append((record.id, name))
        return result
