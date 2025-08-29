from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsUsageTracking(models.Model):
    _name = 'records.usage.tracking'
    _description = 'Records Usage Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Usage Record", required=True, copy=False, readonly=True, default=lambda self: _('New'), index=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # USAGE DETAILS
    # ============================================================================
    date = fields.Date(string='Usage Date', required=True, default=fields.Date.context_today, tracking=True)
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('pickup', 'Pickup'),
        ('destruction', 'Destruction'),
        ('other', 'Other'),
    ], string="Service Type", required=True, tracking=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0, tracking=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", ondelete='restrict')
    
    # ============================================================================
    # FINANCIALS
    # ============================================================================
    cost = fields.Monetary(string='Cost', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)

    # ============================================================================
    # RELATIONSHIPS & CONTEXT
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    product_id = fields.Many2one('product.product', string="Service Product", ondelete='restrict')
    invoice_line_id = fields.Many2one('account.move.line', string="Invoice Line", readonly=True)
    
    # Generic relation to link to the source document (e.g., work order, destruction order)
    res_model = fields.Char(string="Source Model", readonly=True)
    res_id = fields.Integer(string="Source Record ID", readonly=True)
    source_document = fields.Reference(selection='_selection_source_document', string="Source Document", compute='_compute_source_document', readonly=True)

    notes = fields.Text(string='Notes')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.usage.tracking') or _('New')
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.state == 'billed':
                raise UserError(_("You cannot delete a usage record that has already been billed."))
        return super().unlink()

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_source_document(self):
        for record in self:
            if record.res_model and record.res_id:
                record.source_document = f"{record.res_model},{record.res_id}"
            else:
                record.source_document = False

    @api.model
    def _selection_source_document(self):
        """Provide a selection of models that can be sources of usage."""
        # This can be expanded as more source models are integrated
        return [
            ('records.retrieval.work.order', 'Retrieval Work Order'),
            ('records.destruction', 'Destruction Order'),
            ('records.container', 'Container'),
            ('portal.request', 'Portal Request'),
        ]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Usage record cancelled."))
