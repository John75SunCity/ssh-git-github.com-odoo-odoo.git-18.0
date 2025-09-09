import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBale(models.Model):
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Bale Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    bale_number = fields.Char(
        string="Bale Number", readonly=True, copy=False, help="Sequential bale number for identification"
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('weighed', 'Weighed'),
        ('in_stock', 'In Stock'),
        ('shipped', 'Shipped'),
        ('recycled', 'Recycled'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    weight = fields.Float(string="Weight (kg)", tracking=True)
    weigh_date = fields.Datetime(string="Weigh Date", tracking=True)

    paper_grade = fields.Selection([
        ('wht', 'WHT'),
        ('mix', 'MIX'),
        ('occ', 'OCC (Cardboard)'),
    ], string="Paper Grade", tracking=True)

    location_id = fields.Many2one('records.location', string="Current Location", tracking=True)
    shipment_id = fields.Many2one('paper.load.shipment', string="Shipment", readonly=True)
    load_id = fields.Many2one('load', string="Load")

    inspection_ids = fields.One2many('paper.bale.inspection', 'bale_id', string="Inspections")
    inspection_count = fields.Integer(compute='_compute_inspection_count', string="Inspection Count")

    movement_ids = fields.One2many('paper.bale.movement', 'bale_id', string="Movements")
    movement_count = fields.Integer(compute='_compute_movement_count', string="Movement Count")

    # Source Information
    source_type = fields.Selection([
        ('daily_route', 'Daily Route Consolidation'),
        ('purge_project', 'One-Time Purge Project'),
        ('drop_off', 'Customer Drop-off'),
        ('internal', 'Internal Documents'),
        ('other', 'Other'),
    ], string="Source Type", tracking=True, help="The general origin of the paper in this bale.")
    source_date = fields.Date(string="Source Consolidation Date", tracking=True, help="The date the source material was consolidated and shredded.")
    source_notes = fields.Text(string="Source Notes", help="Optional notes about the source, such as route numbers, project names, or customer details.")

    notes = fields.Text(string="Bale Notes")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        for bale in self:
            bale.inspection_count = len(bale.inspection_ids)

    @api.depends('movement_ids')
    def _compute_movement_count(self):
        for bale in self:
            bale.movement_count = len(bale.movement_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_inspections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspections for %s', self.name),
            'res_model': 'paper.bale.inspection',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    def action_view_movements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Movements for %s', self.name),
            'res_model': 'paper.bale.movement',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals["name"] = self.env["ir.sequence"].next_by_code("records_management.bale") or _("New")
                # Set bale_number to just the sequential number part for easy reference
                if vals.get("name") and vals["name"] != _("New"):
                    # Extract the number part from the sequence (e.g., "BALE-2025-00001" -> "00001")
                    match = re.search(r"-(\d+)$", vals["name"])
                    if match:
                        vals["bale_number"] = match.group(1)
                    else:
                        vals["bale_number"] = vals["name"]
        return super().create(vals_list)

    @api.constrains('weight')
    def _check_weight(self):
        for bale in self:
            if bale.weight < 0:
                raise ValidationError(_("Bale weight cannot be negative."))

    # ------------------------------------------------------------------
    # Placeholder button actions migrated from placeholder file
    # ------------------------------------------------------------------
    def action_weigh_bale(self):
        self.ensure_one()
        return False  # Future implementation: open weigh wizard

    def action_load_trailer(self):
        self.ensure_one()
        return False  # Future implementation: assign to trailer

    def action_view_source_documents(self):
        self.ensure_one()
        return False  # Future implementation

    def action_view_trailer_info(self):
        self.ensure_one()
        return False  # Future: open trailer record

    def action_view_weight_history(self):
        self.ensure_one()
        return False  # Future: open weight history lines

    # ------------------------------------------------------------------
    # ADDITIONAL VIEW BUTTON STUBS (quality / inspection / labels / reports)
    # ------------------------------------------------------------------
    def action_quality_inspection(self):  # XML button placeholder
        self.ensure_one()
        # Future: open inspection wizard (paper.bale.inspection.wizard)
        return False

    def action_view_inspection_details(self):  # XML button placeholder
        self.ensure_one()
        # Future: open existing inspection records tree
        return {
            'type': 'ir.actions.act_window',
            'name': _("Inspection Details %s") % self.name,
            'res_model': 'paper.bale.inspection',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    def action_print_label(self):  # XML button placeholder
        self.ensure_one()
        # Future: generate QWeb PDF / ZPL output for bale label
        return False

    def action_view_weight_tickets(self):  # XML button placeholder
        self.ensure_one()
        # Future: open related weight ticket records (model TBD)
        return False

    def action_view_revenue_report(self):  # XML button placeholder
        self.ensure_one()
        # Future: open reporting action or pivot view filtered by bale
        return False
