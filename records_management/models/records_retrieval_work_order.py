from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsRetrievalWorkOrder(models.Model):
    _name = 'records.retrieval.work.order'
    _description = 'Records Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Work Order', required=True, readonly=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned To')
    completion_date = fields.Datetime(string='Completion Date', help="Date and time when the retrieval was completed")
    delivery_method = fields.Selection([('scan', 'Scan & Email'), ('physical', 'Physical Delivery')], string='Delivery Method')

    # Link to retrieval team (for One2many in maintenance.team)
    retrieval_team_id = fields.Many2one(comodel_name='maintenance.team', string='Retrieval Team')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', compute='_compute_currency_id', store=True)

    # ============================================================================
    # BARCODE SCANNING FIELDS
    # ============================================================================
    scanned_barcode_ids = fields.Many2many(
        comodel_name='records.container',
        relation='retrieval_work_order_scanned_barcodes',
        column1='work_order_id',
        column2='container_id',
        string='Scanned Containers',
        help="Containers that were scanned during this retrieval"
    )
    scanned_count = fields.Integer(
        string='Scanned Items',
        compute='_compute_scanned_count',
        store=True
    )
    last_scan_time = fields.Datetime(string='Last Scan', readonly=True)

    # ============================================================================
    # METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.retrieval.work.order') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Auto-set completion_date when state changes to completed"""
        if 'state' in vals and vals['state'] == 'completed':
            vals['completion_date'] = fields.Datetime.now()
        return super().write(vals)

    @api.depends('company_id')
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record.company_id.currency_id

    @api.depends('scanned_barcode_ids')
    def _compute_scanned_count(self):
        """Count of containers scanned during retrieval."""
        for order in self:
            order.scanned_count = len(order.scanned_barcode_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_progress(self):
        """Start the retrieval work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be started."))
        self.write({'state': 'in_progress'})
        return True

    def action_complete(self):
        """Complete the retrieval work order"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only work orders in progress can be completed."))
        self.write({
            'state': 'completed',
            'completion_date': fields.Datetime.now()
        })
        return True

    def action_cancel(self):
        """Cancel the retrieval work order"""
        self.ensure_one()
        if self.state in ['completed']:
            raise UserError(_("Completed work orders cannot be cancelled."))
        self.write({'state': 'cancelled'})
        return True

    def action_scan_barcode(self, barcode_value):
        """
        Scan a barcode during retrieval.
        Works with USB scanners (types into field) or manual entry.
        
        Args:
            barcode_value (str): The barcode to scan
            
        Returns:
            dict: Scan result with success/message
        """
        self.ensure_one()
        
        if self.state not in ['draft', 'in_progress']:
            return {
                'success': False,
                'message': _('Work order must be active to scan barcodes')
            }
        
        # Find container
        container = self.env['records.container'].search([
            '|',
            ('barcode', '=', barcode_value),
            ('temp_barcode', '=', barcode_value)
        ], limit=1)
        
        if not container:
            return {
                'success': False,
                'message': _('Container not found: %s') % barcode_value
            }
        
        # Check duplicate
        if container in self.scanned_barcode_ids:
            return {
                'success': False,
                'message': _('Already scanned: %s') % container.name,
                'warning': True
            }
        
        # Add to scanned list
        self.write({
            'scanned_barcode_ids': [(4, container.id)],
            'last_scan_time': fields.Datetime.now(),
        })
        
        # Log
        self.message_post(
            body=_('Retrieved container: %s (Barcode: %s)') % (container.name, barcode_value),
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'success': True,
            'message': _('Retrieved: %s') % container.name,
            'container_id': container.id,
            'total_scanned': len(self.scanned_barcode_ids)
        }

    def action_reset_to_draft(self):
        """Reset work order to draft state"""
        self.ensure_one()
        if self.state not in ['cancelled']:
            raise UserError(_("Only cancelled work orders can be reset to draft."))
        self.write({'state': 'draft'})
        return True
