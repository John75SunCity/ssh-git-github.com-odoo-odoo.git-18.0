from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class FileRetrievalWorkOrder(models.Model):
    _name = 'file.retrieval.work.order'
    _description = 'File Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    priority = fields.Selection()
    partner_id = fields.Many2one()
    portal_request_id = fields.Many2one()
    request_description = fields.Text()
    retrieval_item_ids = fields.One2many()
    item_count = fields.Integer()
    estimated_pages = fields.Integer()
    container_ids = fields.Many2many()
    location_ids = fields.Many2many()
    access_coordination_needed = fields.Boolean()
    scheduled_date = fields.Datetime()
    estimated_completion_date = fields.Datetime()
    actual_start_date = fields.Datetime()
    actual_completion_date = fields.Datetime()
    delivery_method = fields.Selection()
    packaging_type = fields.Selection()
    delivery_address_id = fields.Many2one()
    delivery_instructions = fields.Text()
    progress_percentage = fields.Float()
    files_located_count = fields.Integer()
    files_retrieved_count = fields.Integer()
    files_quality_approved_count = fields.Integer()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    coordinator_id = fields.Many2one()
    rate_id = fields.Many2one('base.rate')
    invoice_id = fields.Many2one('account.move')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name') = self.env['ir.sequence'].next_by_code()
                        'file.retrieval.work.order') or _('New'
            return super().create(vals_list)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            for record in self:
                if record.partner_id and record.item_count:
                    record.display_name = _("%s - %s (%s files)",
                        record.name, record.partner_id.name, record.item_count
                elif record.partner_id:
                    record.display_name = _("%s - %s", record.name, record.partner_id.name)
                else:
                    record.display_name = record.name or _("New File Retrieval")


    def _compute_item_metrics(self):
            for record in self:
                items = record.retrieval_item_ids
                record.item_count = len(items)
                record.estimated_pages = sum(items.mapped('estimated_pages')) if items else 0:

    def _compute_estimated_completion(self):
            for record in self:
                if record.scheduled_date and record.item_count:
                    # Estimate 2 hours per file plus 4 hours base time
                    estimated_hours = 4 + (record.item_count * 2)
                    record.estimated_completion_date = record.scheduled_date + timedelta(hours=estimated_hours)
                else:
                    record.estimated_completion_date = False


    def _compute_progress(self):
            for record in self:
                if record.item_count > 0:
                    record.progress_percentage = (record.files_retrieved_count / record.item_count) * 100
                else:
                    record.progress_percentage = 0.0

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm(self):
            """Confirm the work order"""
            self.ensure_one()
            if self.state != 'draft':
                raise UserError(_("Only draft work orders can be confirmed"))

            self.write({'state': 'confirmed'})
            self.message_post()
                body=_("File retrieval work order confirmed for %s", self.partner_id.name),:
                message_type='notification'

            return True


    def action_start_locating(self):
            """Start file location process"""
            self.ensure_one()
            if self.state != 'confirmed':
                raise UserError(_("Only confirmed work orders can start file location"))

            self.write({)}
                'state': 'locating',
                'actual_start_date': fields.Datetime.now()

            self.message_post()
                body=_("Started file location process"),
                message_type='notification'

            return True


    def action_complete(self):
            """Complete the work order"""
            self.ensure_one()
            if self.state != 'delivered':
                raise UserError(_("Only delivered work orders can be completed"))

            self.write({)}
                'state': 'completed',
                'actual_completion_date': fields.Datetime.now()

            self.message_post()
                body=_("File retrieval work order completed successfully"),
                message_type='notification'

            return True


    def action_view_retrieval_items(self):
            """View retrieval items in a separate window"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Retrieval Items"),
                "res_model": "file.retrieval.work.order.item",
                "view_mode": "tree,form",
                "domain": [("work_order_id", "=", self.id)],
                "context": {"default_work_order_id": self.id},
                "target": "current",


        # ============================================================================
            # BUSINESS WORKFLOW METHODS
        # ============================================================================

    def _update_progress_metrics(self):
            """Update progress metrics based on item status"""
            for record in self:
                items = record.retrieval_item_ids
                if items:
                    record.files_located_count = len()
                        items.filtered()
                            lambda r: r.status
                            in []
                                "located",
                                "retrieved",
                                "quality_checked",
                                "packaged",



                    record.files_retrieved_count = len()
                        items.filtered()
                            lambda r: r.status
                            in ["retrieved", "quality_checked", "packaged"]


                    record.files_quality_approved_count = len()
                        items.filtered()
                            lambda r: r.status in ["quality_checked", "packaged"]




    def _create_naid_audit_log(self, event_type):
            """Create NAID audit log for work order events""":
            if self.env["ir.module.module"].search(:)
                [("name", "=", "records_management"), ("state", "=", "installed")]

                self.env["naid.audit.log"].create()
                    {}
                        "event_type": event_type,
                        "model_name": self._name,
                        "record_id": self.id,
                        "partner_id": self.partner_id.id,
                        "description": _("Work order: %s", self.name),
                        "user_id": self.env.user.id,
                        "timestamp": fields.Datetime.now()))))))))))))))))))

