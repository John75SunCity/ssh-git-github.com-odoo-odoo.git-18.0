from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ContainerRetrieval(models.Model):
    _name = 'container.retrieval'
    _description = 'Container Retrieval Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # Core fields from document.retrieval.item
    name = fields.Char(string='Retrieval Reference', required=True, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # Container-specific fields
    container_id = fields.Many2one(comodel_name='records.container', string='Container', required=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True)
    location_id = fields.Many2one(comodel_name='records.location', string='Current Location')
    storage_location_id = fields.Many2one(comodel_name='records.location', string='Storage Location')

    # Status and workflow
    status = fields.Selection([
        ('pending', 'Pending'),
        ('searching', 'Searching'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('not_found', 'Not Found')
    ], string='Status', default='pending', tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')

    # Timing and logistics
    estimated_time = fields.Float(string='Estimated Time (hours)')
    actual_time = fields.Float(string='Actual Time (hours)')
    retrieval_date = fields.Datetime(string='Retrieved Date')
    retrieved_by_id = fields.Many2one(comodel_name='res.users', string='Retrieved By')

    # Cost tracking
    retrieval_cost = fields.Monetary(
        string="Retrieval Cost", compute="_compute_retrieval_cost", currency_field="currency_id"
    )
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', compute='_compute_currency_id')

    # Display and related fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.depends('container_id.currency_id', 'company_id.currency_id')
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record.company_id.currency_id or self.env.company.currency_id

    @api.depends('partner_id')
    def _compute_retrieval_cost(self):
        for record in self:
            # Container retrieval cost logic
            record.retrieval_cost = 25.0  # Default container retrieval cost

    @api.depends('name', 'container_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.container_id:
                record.display_name = f"{record.name} - {record.container_id.name}"
            else:
                record.display_name = record.name or "New Container Retrieval"

    def action_locate_container(self):
        """Mark container as located"""
        self.ensure_one()
        for record in self:
            if record.status != 'pending':
                raise UserError(_("Only pending retrievals can be located."))
            record.write({
                'status': 'located',
                'retrieval_date': fields.Datetime.now(),
                'retrieved_by_id': self.env.user.id
            })
            record.message_post(body=_("Container located by %s", self.env.user.name))

    def action_retrieve_container(self):
        """Mark container as retrieved"""
        self.ensure_one()
        for record in self:
            if record.status != 'located':
                raise UserError(_("Container must be located before retrieval."))
            record.write({'status': 'retrieved'})
            record.message_post(body=_("Container retrieved by %s", self.env.user.name))
