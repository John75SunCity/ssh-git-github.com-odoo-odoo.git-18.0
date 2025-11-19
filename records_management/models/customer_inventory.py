"""Customer Inventory Model (sanitized rewrite to normalize indentation)."""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CustomerInventory(models.Model):
    _name = 'customer.inventory'
    _description = 'Customer Inventory'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, name'
    _rec_name = 'name'

    # CORE & WORKFLOW ---------------------------------------------------------
    name = fields.Char(string='Inventory Reference', required=True, copy=False, readonly=True, default=lambda self: "New")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    inventory_date = fields.Date(string='Inventory Date', default=fields.Date.context_today, required=True)
    completion_date = fields.Datetime(string='Completion Date', readonly=True)
    last_updated = fields.Datetime(string='Last Updated', readonly=True, copy=False,
                                   help="Timestamp of the last modification to any inventory line or core field")
    status_detail = fields.Char(string='Status Detail', help="Extended textual status used in advanced views")
    total_documents = fields.Integer(string='Total Documents', compute='_compute_inventory_totals', store=True,
                                     help="Aggregate of file counts across all inventory lines")

    # RELATIONSHIPS -----------------------------------------------------------
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one(comodel_name='records.department', string='Department', tracking=True,
                                    help="Optional: Filter inventory by a specific customer department.")

    # INVENTORY DETAILS -------------------------------------------------------
    inventory_line_ids = fields.One2many('customer.inventory.line', 'inventory_id', string='Inventory Lines')
    total_containers = fields.Integer(string='Total Containers', compute='_compute_inventory_totals', store=True)
    total_files = fields.Integer(string='Total Files', compute='_compute_inventory_totals', store=True)
    verified_containers = fields.Integer(string='Verified Containers', compute='_compute_verification_stats', store=True)
    verification_percentage = fields.Float(string='Verification %', compute='_compute_verification_stats', store=True)
    notes = fields.Text(string='Notes')

    # ENHANCED FEATURES -------------------------------------------------------
    inventory_type = fields.Selection([
        ('full', 'Full Inventory'),
        ('sample', 'Sample Inventory'),
        ('variance', 'Variance Check'),
        ('audit', 'Audit Inventory')
    ], string='Inventory Type', default='full', required=True)

    cycle_count = fields.Boolean(string='Cycle Count', help="Mark this as a cycle count inventory")
    previous_inventory_id = fields.Many2one(comodel_name='customer.inventory', string='Previous Inventory',
                                            help="Reference to previous inventory for variance tracking")

    # Variance tracking
    has_variances = fields.Boolean(string='Has Variances', compute='_compute_variances', store=True)
    variance_count = fields.Integer(string='Variance Count', compute='_compute_variances', store=True)

    # Location and filter options
    location_ids = fields.Many2many(
        'stock.location',
        relation='customer_inventory_location_rel',
        column1='inventory_id',
        column2='location_id',
        string='Locations',
        help="Limit inventory to specific locations"
    )
    container_type_ids = fields.Many2many(
        'records.container.type',
        relation='customer_inventory_container_type_rel',
        column1='inventory_id',
        column2='container_type_id',
        string='Container Types',
        help="Limit inventory to specific container types"
    )

    # Workflow fields
    reviewer_id = fields.Many2one(comodel_name='res.users', string='Reviewer', tracking=True)
    review_notes = fields.Text(string='Review Notes')

    # COMPUTE METHODS ---------------------------------------------------------
    @api.depends('inventory_line_ids.container_id', 'inventory_line_ids.file_count')
    def _compute_inventory_totals(self):
        for record in self:
            record.total_containers = len(record.inventory_line_ids.mapped('container_id'))
            record.total_files = sum(record.inventory_line_ids.mapped('file_count'))
            record.total_documents = record.total_files

    @api.depends('inventory_line_ids.verified')
    def _compute_verification_stats(self):
        for record in self:
            verified_lines = record.inventory_line_ids.filtered('verified')
            record.verified_containers = len(verified_lines)
            record.verification_percentage = (
                (record.verified_containers / record.total_containers) * 100
                if record.total_containers else 0.0
            )

    @api.depends('inventory_line_ids.has_variance')
    def _compute_variances(self):
        for record in self:
            variance_lines = record.inventory_line_ids.filtered('has_variance')
            record.variance_count = len(variance_lines)
            record.has_variances = record.variance_count > 0

    # VALIDATION METHODS ------------------------------------------------------
    @api.constrains('inventory_date')
    def _check_inventory_date(self):
        for record in self:
            if record.inventory_date > fields.Date.context_today(self):
                raise ValidationError(_("Inventory date cannot be in the future."))

    @api.constrains('location_ids', 'department_id')
    def _check_location_department_consistency(self):
        for record in self:
            if record.department_id and record.location_ids:
                invalid_locations = record.location_ids.filtered(
                    lambda l, record=record: l.department_id and l.department_id != record.department_id
                )
                if invalid_locations:
                    raise ValidationError(_("Selected locations must belong to the same department: %s") % ', '.join(invalid_locations.mapped('name')))

    # ACTION METHODS ----------------------------------------------------------
    def action_generate_inventory(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("You can only generate inventory for a draft record."))
        self.inventory_line_ids.unlink()
        domain = [('partner_id', '=', self.partner_id.id), ('state', '!=', 'destroyed')]
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
        if self.container_type_ids:
            domain.append(('container_type_id', 'in', self.container_type_ids.ids))
        containers = self.env['records.container'].search(domain)
        if not containers:
            raise UserError(_("No containers found matching the specified criteria."))
        lines_to_create = []
        for container in containers:
            line_vals = {
                'inventory_id': self.id,
                'container_id': container.id,
                'location_id': container.location_id.id,
                'file_count': container.file_count,
                'expected_file_count': container.file_count,
            }
            if self.previous_inventory_id:
                prev_line = self.previous_inventory_id.inventory_line_ids.filtered(
                    lambda l, container=container: l.container_id == container
                )
                if prev_line:
                    line_vals['previous_file_count'] = prev_line.file_count
            lines_to_create.append(line_vals)
        self.env['customer.inventory.line'].create(lines_to_create)
        self.write({'state': 'in_progress'})
        self._touch_last_updated()
        self.message_post(body=_("Inventory lines generated for %s containers using %s inventory type.") % (
            len(containers), dict(self._fields['inventory_type'].selection)[self.inventory_type]))

    def action_bulk_verify(self):
        self.ensure_one()
        unverified_lines = self.inventory_line_ids.filtered(lambda l: not l.verified)
        if not unverified_lines:
            raise UserError(_("All lines are already verified."))
        unverified_lines.write({'verified': True, 'verification_date': fields.Datetime.now()})
        self.message_post(body=("Bulk verification completed for %s lines.") % len(unverified_lines))
        self._touch_last_updated()
        return True

    def action_submit_for_review(self):
        self.ensure_one()
        if self.verification_percentage < 100:
            raise UserError(_("All containers must be verified before submitting for review."))
        self.write({'state': 'review'})
        self.message_post(body=_("Inventory submitted for review."))
        self._touch_last_updated()

    def action_approve(self):
        self.ensure_one()
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can approve inventories."))
        self.write({
            'state': 'completed',
            'reviewer_id': self.env.user.id,
            'completion_date': fields.Datetime.now()
        })
        self.message_post(body=_("Inventory approved and completed."))
        self._touch_last_updated()

    def action_complete(self):
        self.ensure_one()
        self.write({'state': 'completed', 'completion_date': fields.Datetime.now()})
        self.message_post(body=_("Inventory marked as completed."))
        self._touch_last_updated()

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Inventory cancelled."))
        self._touch_last_updated()

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Inventory reset to draft."))
        self._touch_last_updated()

    def action_export_to_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.customer_inventory_excel',
            'report_type': 'xlsx',
            'data': {'inventory_id': self.id},
            'context': self.env.context,
        }

    def action_view_variances(self):
        self.ensure_one()
        variance_lines = self.inventory_line_ids.filtered('has_variance')
        return {
            'name': _('Inventory Variances'),
            'type': 'ir.actions.act_window',
            'res_model': 'customer.inventory.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', variance_lines.ids)],
            'context': {'default_inventory_id': self.id}
        }

    # ORM OVERRIDES -----------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                partner_id = vals.get('partner_id')
                inventory_type = vals.get('inventory_type', 'full')
                if partner_id:
                    partner = self.env['res.partner'].browse(partner_id)
                    sequence_code = f'customer.inventory.{inventory_type}'
                    sequence_name = self.env['ir.sequence'].with_context(force_company=self.env.company.id).next_by_code(sequence_code) \
                        or self.env['ir.sequence'].next_by_code('customer.inventory') or _('New')
                    type_abbrev = {'full': 'FULL', 'sample': 'SMPL', 'variance': 'VAR', 'audit': 'AUD'}.get(inventory_type, 'FULL')
                    vals['name'] = f"{partner.name or 'Unknown'} - {type_abbrev} - {sequence_name}"
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('customer.inventory') or _('New')
        records = super().create(vals_list)
        for record in records:
            record.message_post(body=("Inventory created with type: %s") % dict(record._fields['inventory_type'].selection)[record.inventory_type])
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_touch'):
            return res
        tracked_fields = {
            'state', 'inventory_date', 'partner_id', 'department_id', 'inventory_type',
            'reviewer_id', 'cycle_count', 'previous_inventory_id'
        }
        if any(field in vals for field in tracked_fields):
            self._touch_last_updated()
        return res

    # INTERNAL HELPERS --------------------------------------------------------
    def _touch_last_updated(self):
        """Safely update last_updated avoiding recursion."""
        self.with_context(skip_touch=True).write({'last_updated': fields.Datetime.now()})
