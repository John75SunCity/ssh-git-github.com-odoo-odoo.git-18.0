from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields


class BarcodeGenerationHistory(models.Model):
    _name = 'barcode.generation.history'
    _description = 'Barcode Generation History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'generation_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    product_id = fields.Many2one('barcode.product', string='Product')
    barcode_generated = fields.Char(string='Generated Barcode')
    generation_date = fields.Datetime()
    generated_by_id = fields.Many2one()
    generation_method = fields.Selection()
    barcode_format = fields.Selection()
    sequence_number = fields.Integer(string='Sequence Number')
    batch_id = fields.Char(string='Batch ID')
    printed_date = fields.Datetime(string='Printed Date')
    applied_date = fields.Datetime(string='Applied Date')
    print_count = fields.Integer(string='Print Count')
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    partner_id = fields.Many2one()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_generate(self):
            """Mark as generated"""
            self.ensure_one()
            self.write({"state": "generated", "generation_date": fields.Datetime.now()})


    def action_print(self):
            """Mark as printed"""
            self.ensure_one()
            self.write()
                {}
                    "state": "printed",
                    "printed_date": fields.Datetime.now(),
                    "print_count": self.print_count + 1,




    def action_apply(self):
            """Mark as applied"""
            self.ensure_one()
            self.write({"state": "applied", "applied_date": fields.Datetime.now()})
