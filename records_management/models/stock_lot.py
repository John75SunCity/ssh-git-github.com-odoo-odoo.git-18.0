from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_box = fields.Boolean(
        string="Is a Records Box",
        help="Check this if the lot represents a physical records management box."
    )
    document_count = fields.Integer(
        string="Document Count",
        compute='_compute_document_count',
        store=True,
        help="Number of individual documents or files stored in this box."
    )
    destruction_eligible = fields.Boolean(
        string="Eligible for Destruction",
        default=False,
        help="Indicates if this box has passed its retention period and can be destroyed."
    )
    retention_date = fields.Date(
        string="Retention Expiry Date",
        tracking=True,
        help="The date after which this box can be considered for destruction."
    )
    destruction_date = fields.Date(
        string="Actual Destruction Date",
        readonly=True,
        tracking=True,
        help="The date this box was physically destroyed."
    )
    last_audit_date = fields.Date(
        string="Last Audit Date",
        readonly=True,
        help="Date of the last physical or digital audit of this box."
    )
    audit_notes = fields.Text(string='Audit Notes')

    # ------------------------------------------------------------------
    # VIRTUAL BOOLEAN FILTERS (replace relativedelta in XML domains)
    # ------------------------------------------------------------------
    created_last_7d = fields.Boolean(compute='_compute_recency_flags', search='_search_created_last_7d', string='Created Last 7 Days')
    created_last_30d = fields.Boolean(compute='_compute_recency_flags', search='_search_created_last_30d', string='Created Last 30 Days')
    retention_due_30d = fields.Boolean(compute='_compute_retention_flags', search='_search_retention_due_30d', string='Retention Due ≤30d')

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    # Assuming a model 'records.document' exists to track individual documents
    document_ids = fields.One2many('records.document', 'lot_id', string="Documents")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute number of documents associated with this lot."""
        for lot in self:
            lot.document_count = len(lot.document_ids)

    def _compute_recency_flags(self):
        from datetime import timedelta
        now = fields.Datetime.now()
        cut7 = now - timedelta(days=7)
        cut30 = now - timedelta(days=30)
        for rec in self:
            # create_date is datetime; treat missing as False
            cdate = rec.create_date
            rec.created_last_7d = bool(cdate and cdate >= cut7)
            rec.created_last_30d = bool(cdate and cdate >= cut30)

    def _compute_retention_flags(self):
        from datetime import timedelta
        today = fields.Date.today()
        soon = today + timedelta(days=30)
        for rec in self:
            rd = rec.retention_date
            rec.retention_due_30d = bool(rd and today <= rd <= soon)

    # -----------------------------
    # SEARCH HELPERS
    # -----------------------------
    def _search_created_last_7d(self, operator, value):
        from datetime import timedelta
        if operator not in ('=', '=='):
            return [('id', '!=', 0)]
        boundary = fields.Datetime.now() - timedelta(days=7)
        return [('create_date', '>=', boundary)] if value else ['|', ('create_date', '=', False), ('create_date', '<', boundary)]

    def _search_created_last_30d(self, operator, value):
        from datetime import timedelta
        if operator not in ('=', '=='):
            return [('id', '!=', 0)]
        boundary = fields.Datetime.now() - timedelta(days=30)
        return [('create_date', '>=', boundary)] if value else ['|', ('create_date', '=', False), ('create_date', '<', boundary)]

    def _search_retention_due_30d(self, operator, value):
        from datetime import timedelta
        if operator not in ('=', '=='):
            return [('id', '!=', 0)]
        today = fields.Date.today()
        soon = today + timedelta(days=30)
        if value:
            return [('retention_date', '>=', today), ('retention_date', '<=', soon)]
        return ['|', ('retention_date', '=', False), ('retention_date', '>', soon)]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_destruction_eligible(self):
        """Mark lot as eligible for destruction."""
        self.ensure_one()
        if self.retention_date and self.retention_date > fields.Date.today():
            raise UserError(
                _(
                    "This box cannot be marked for destruction until its retention period expires on %s.",
                    self.retention_date,
                )
            )
        self.write({"destruction_eligible": True})
        self.message_post(body=_("Lot marked as eligible for destruction by %s.", self.env.user.name))
        return True

    def action_view_documents(self):
        """Opens a view to see all documents within this box."""
        self.ensure_one()
        return {
            "name": _("Documents in Box %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.document_ids.ids)],
            "context": {"default_lot_id": self.id},
        }

    # Placeholder view buttons (XML object buttons)
    def action_view_quants(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quants'),
            'res_model': 'stock.quant',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'target': 'current',
        }

    def action_view_stock_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Moves'),
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'target': 'current',
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('retention_date', 'destruction_date')
    def _check_dates(self):
        """Validate retention and destruction dates."""
        for lot in self:
            if lot.retention_date and lot.destruction_date and lot.destruction_date < lot.retention_date:
                raise ValidationError(_("The destruction date cannot be earlier than the retention expiry date."))
