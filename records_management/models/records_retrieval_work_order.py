from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsRetrievalWorkOrder(models.Model):
    _name = 'records.retrieval.work.order'
    _description = 'Records Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.invoice.mixin']

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
    notes = fields.Text(string='Notes', help="Internal notes about this retrieval request")

    # Link to retrieval team (for One2many in maintenance.team)
    retrieval_team_id = fields.Many2one(comodel_name='maintenance.team', string='Retrieval Team')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', compute='_compute_currency_id', store=True)

    # FSM Integration
    fsm_task_id = fields.Many2one('project.task', string='FSM Task', readonly=True, copy=False)
    fsm_task_count = fields.Integer(compute='_compute_fsm_task_count', string='FSM Tasks')

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

    def _compute_fsm_task_count(self):
        """Count linked FSM tasks"""
        for order in self:
            order.fsm_task_count = 1 if order.fsm_task_id else 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_progress(self):
        """Start the retrieval work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be started."))
        self.write({'state': 'in_progress'})
        
        # Auto-create FSM task
        if not self.fsm_task_id:
            self.action_create_fsm_task()
        
        return True

    def action_create_fsm_task(self):
        """Create FSM task with retrieval worksheet"""
        self.ensure_one()
        
        if self.fsm_task_id:
            raise UserError(_("FSM task already exists for this work order"))
        
        # Get or create FSM project
        fsm_project = self.env.ref('records_management_fsm.project_field_service', raise_if_not_found=False)
        if not fsm_project:
            # Create default FSM project
            fsm_project = self.env['project.project'].create({
                'name': 'Field Service',
                'is_fsm': True,
                'allow_timesheets': True,
            })
        
        # Create FSM task
        task_vals = {
            'name': f"Retrieval: {self.name}",
            'project_id': fsm_project.id,
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id if self.user_id else False,
            'date_deadline': fields.Date.today(),
            'retrieval_work_order_id': self.id,
            'container_ids': [(6, 0, self.scanned_barcode_ids.ids)],
        }
        
        task = self.env['project.task'].create(task_vals)
        self.fsm_task_id = task.id
        
        # Create worksheet from template
        template = self.env.ref('records_management_fsm.worksheet_template_retrieval', raise_if_not_found=False)
        if template:
            self.env['fsm.worksheet.instance'].create({
                'task_id': task.id,
                'template_id': template.id,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Task'),
            'res_model': 'project.task',
            'res_id': task.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_fsm_task(self):
        """Open related FSM task"""
        self.ensure_one()
        if not self.fsm_task_id:
            return self.action_create_fsm_task()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Task'),
            'res_model': 'project.task',
            'res_id': self.fsm_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_complete(self):
        """
        Complete the retrieval work order.
        
        Updates all scanned containers from 'in' to 'out' state,
        indicating they have been retrieved from storage and are now with the customer.
        Also creates billing charges for retrieval services.
        """
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only work orders in progress can be completed."))
        
        retrieved_count = 0
        already_out = 0
        
        # Update all scanned containers to 'out' state
        for container in self.scanned_barcode_ids:
            if container.state == 'in':
                # Create billing charge for retrieval service
                retrieval_product = self.env.ref(
                    'records_management.product_retrieval_service',
                    raise_if_not_found=False
                )
                if retrieval_product and container.partner_id:
                    # Get retrieval rate
                    retrieval_rate = container._get_retrieval_rate(retrieval_product)
                    
                    # Find or create billing record for this period
                    today = fields.Date.today()
                    billing = self.env['records.billing'].sudo().search([
                        ('partner_id', '=', container.partner_id.id),
                        ('state', '=', 'draft'),
                        ('date', '>=', today.replace(day=1)),
                    ], limit=1)
                    if not billing:
                        billing_config = self.env['records.billing.config'].sudo().search([
                            ('company_id', '=', self.env.company.id),
                        ], limit=1)
                        if billing_config:
                            billing = self.env['records.billing'].sudo().create({
                                'partner_id': container.partner_id.id,
                                'date': today,
                                'billing_config_id': billing_config.id,
                                'state': 'draft',
                            })
                    if billing:
                        self.env['advanced.billing.line'].sudo().create({
                            'billing_id': billing.id,
                            'name': _('Container Retrieval - %s') % container.name,
                            'product_id': retrieval_product.id,
                            'quantity': 1,
                            'amount': retrieval_rate,
                            'type': 'service',
                        })
                
                # Update container state to 'out'
                container.write({
                    'state': 'out',
                    'last_access_date': fields.Date.today()
                })
                container.message_post(
                    body=_("Container retrieved - Work Order: %s") % self.name
                )
                retrieved_count += 1
            elif container.state == 'out':
                already_out += 1
        
        # Complete the work order
        self.write({
            'state': 'completed',
            'completion_date': fields.Datetime.now()
        })
        
        # Return notification with results
        if retrieved_count > 0:
            message = _("%d container(s) marked as 'Out' (retrieved)") % retrieved_count
            if already_out > 0:
                message += _(" (%d already out)") % already_out
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Retrieval Complete'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
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

    def action_open_scanner(self):
        """Open barcode scanner wizard for continuous scanning."""
        self.ensure_one()
        return {
            'name': _('Scan Barcodes'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode.scan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_model': self._name,
                'default_work_order_id': self.id,
            }
        }

    def action_open_camera_scanner(self):
        """
        Directly open the camera barcode scanner (bypasses wizard popup).
        
        This launches the Scanbot SDK camera scanner as a client action.
        Scanned barcodes are automatically sent to action_scan_barcode().
        Perfect for mobile scanning workflows on work orders.
        
        Returns:
            dict: Client action to launch rm_camera_scanner
        """
        self.ensure_one()
        if self.state not in ['draft', 'in_progress']:
            raise UserError(_("Can only scan barcodes for draft or in-progress work orders."))
        return {
            'type': 'ir.actions.client',
            'tag': 'rm_camera_scanner',
            'name': _('Camera Scanner - %s') % self.name,
            'context': {
                'operation_mode': 'work_order',
                'work_order_model': self._name,
                'work_order_id': self.id,
            },
        }

    def action_reset_to_draft(self):
        """Reset work order to draft state"""
        self.ensure_one()
        if self.state not in ['cancelled']:
            raise UserError(_("Only cancelled work orders can be reset to draft."))
        self.write({'state': 'draft'})
        return True

    def action_verify_and_return(self):
        """
        Verify all scanned containers and execute permanent removal (perm-out) workflow.
        
        This is used when customers want to take their items back permanently.
        Creates removal charges only (no shredding fees).
        
        Returns:
            dict: Notification action with results
        """
        self.ensure_one()
        
        # Validate state
        if self.state not in ['in_progress', 'draft']:
            raise UserError(_("Can only verify and return items when work order is active."))
        
        # Check for scanned containers
        if not self.scanned_barcode_ids:
            raise UserError(_("No containers have been scanned for this retrieval."))
        
        returned_count = 0
        failed_containers = []
        
        # Process each scanned container
        for container in self.scanned_barcode_ids:
            # Skip if already returned
            if container.state == 'perm_out':
                continue
            
            try:
                # Execute barcode perm-out workflow (sets state, creates 1 charge, audit log)
                container.action_barcode_perm_out()
                returned_count += 1
            except UserError as e:
                # Collect failures for reporting
                failed_containers.append((container.name, str(e)))
        
        # Auto-close work order if all containers returned
        all_returned = all(c.state == 'perm_out' for c in self.scanned_barcode_ids)
        if all_returned:
            self.write({
                'state': 'completed',
                'completion_date': fields.Datetime.now()
            })
            message = _("✅ All %d container(s) verified and returned to customer.<br/>• Removal charges created ($15/container)<br/>• Work order completed") % returned_count
        else:
            remaining = len(self.scanned_barcode_ids.filtered(lambda c: c.state != 'perm_out'))
            message = _("✅ %d container(s) verified and returned to customer.<br/>• Removal charges created ($15/container)<br/>• %d container(s) remaining") % (
                returned_count,
                remaining
            )
        
        # Add failure details if any
        if failed_containers:
            message += "<br/><br/>⚠️ Failed containers:<br/>"
            for name, error in failed_containers:
                message += "• %s: %s<br/>" % (name, error)
        
        # Post message to chatter
        self.message_post(
            body=message,
            subject=_("Perm-Out Verification Complete"),
            subtype_xmlid='mail.mt_note'
        )
        
        # Return success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Perm-Out Complete'),
                'message': _('%d container(s) returned to customer and billed for removal') % returned_count,
                'type': 'success',
                'sticky': False,
            }
        }
