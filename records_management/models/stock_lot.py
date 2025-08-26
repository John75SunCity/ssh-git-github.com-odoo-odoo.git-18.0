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
        tracking=True,
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

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_destruction_eligible(self):
        """Mark lot as eligible for destruction."""
        self.ensure_one()
        if self.retention_date and self.retention_date > fields.Date.today():
            raise UserError(_("This box cannot be marked for destruction until its retention period expires on %s.") % self.retention_date)
        self.write({"destruction_eligible": True})
        self.message_post(body=_("Lot marked as eligible for destruction by %s.") % self.env.user.name)
        return True

    def action_view_documents(self):
        """Opens a view to see all documents within this box."""
        self.ensure_one()
        return {
            'name': _('Documents in Box %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.document_ids.ids)],
            'context': {'default_lot_id': self.id},
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
