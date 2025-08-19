from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ShreddingInventoryBatch(models.Model):
    _name = 'shredding.inventory.batch'
    _description = 'Shredding Inventory Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority, scheduled_date desc, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Batch Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], string="Priority", default='0')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # DATES & DETAILS
    # ============================================================================
    scheduled_date = fields.Date(string="Scheduled Date", default=fields.Date.context_today, tracking=True)
    completion_date = fields.Date(string="Completion Date", readonly=True)
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")
    processing_instructions = fields.Text(string="Processing Instructions")

    # ============================================================================
    # BATCH CONTENTS & PROGRESS
    # ============================================================================
    picklist_item_ids = fields.One2many('shredding.picklist.item', 'batch_id', string="Picklist Items")
    item_count = fields.Integer(string="Item Count", compute='_compute_progress', store=True)
    picked_count = fields.Integer(string="Picked Count", compute='_compute_progress', store=True)
    completion_percentage = fields.Float(string="Completion (%)", compute='_compute_progress', store=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.inventory.batch') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('picklist_item_ids', 'picklist_item_ids.status')
    def _compute_progress(self):
        for batch in self:
            total_items = len(batch.picklist_item_ids)
            picked_items = len(batch.picklist_item_ids.filtered(lambda item: item.status in ['picked', 'verified']))
            batch.item_count = total_items
            batch.picked_count = picked_items
            batch.completion_percentage = (picked_items / total_items * 100) if total_items > 0 else 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if not self.picklist_item_ids:
            raise UserError(_("Cannot confirm a batch with no items."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Batch confirmed and ready for processing."))

    def action_start_processing(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Batch processing started."))

    def action_done(self):
        self.ensure_one()
        if any(item.status not in ['verified', 'not_found'] for item in self.picklist_item_ids):
            raise UserError(_("All items must be 'Verified' or 'Not Found' before completing the batch."))
        self.write({'state': 'done', 'completion_date': fields.Date.context_today(self)})
        self.message_post(body=_("Batch marked as done."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Batch has been cancelled."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        self.message_post(body=_("Batch reset to draft."))
