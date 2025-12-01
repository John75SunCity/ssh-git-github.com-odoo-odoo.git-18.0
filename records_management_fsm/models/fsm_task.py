# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTaskFSMExtension(models.Model):
    """
    Extension of project.task to support Records Management FSM integration
    """
    _inherit = 'project.task'

    # ============================================================================
    # RECORDS MANAGEMENT FSM FIELDS
    # ============================================================================

    # Container tracking
    container_ids = fields.Many2many(
        'records.container',
        'fsm_task_container_rel',
        'task_id',
        'container_id',
        string="Containers"
    )

    # Destruction type
    destruction_type = fields.Selection(
        [
            ("on_site", "Mobile Shredding"),
            ("off_site", "Off-Site Destruction"),
            ("media_destruction", "Media Destruction"),
            ("hard_drive", "Hard Drive Destruction"),
            ("specialized", "Specialized Destruction"),
        ],
        string="Destruction Type",
    )

    # Weight tracking
    weight_processed = fields.Float(
        string="Weight Processed (kg)",
        help="Total weight of materials processed"
    )

    # Certificate generation
    destruction_certificate_id = fields.Many2one(
        'destruction.certificate',
        string="NAID Destruction Certificate",
        help="Certificate of destruction for this service"
    )

    # Service completion tracking
    service_complete = fields.Boolean(
        string="Service Complete",
        compute='_compute_service_complete',
        store=True
    )

    # Customer satisfaction
    customer_rating = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Fair'),
        ('3', 'Good'),
        ('4', 'Very Good'),
        ('5', 'Excellent')
    ], string="Customer Rating")

    # Worksheet integration
    rm_worksheet_ids = fields.One2many(
        comodel_name='fsm.worksheet.instance',
        inverse_name='task_id',
        string="RM Worksheets"
    )
    worksheet_complete = fields.Boolean(
        string="Worksheet Complete",
        compute='_compute_worksheet_complete',
        store=True
    )

    # Work order links
    retrieval_work_order_id = fields.Many2one(
        comodel_name='records.retrieval.work.order',
        string="Retrieval Work Order"
    )
    destruction_work_order_id = fields.Many2one(
        comodel_name='container.destruction.work.order',
        string="Destruction Work Order"
    )
    pickup_request_id = fields.Many2one(
        comodel_name='pickup.request',
        string="Pickup Request"
    )
    shredding_work_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string="Shredding Work Order"
    )
    portal_request_id = fields.Many2one(
        comodel_name='portal.request',
        string="Portal Request"
    )
    access_work_order_id = fields.Many2one(
        comodel_name='container.access.work.order',
        string="Access Work Order"
    )
    retrieval_work_order_wo_id = fields.Many2one(
        comodel_name='work.order.retrieval',
        string="Retrieval Work Order (WO)"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends('rm_worksheet_ids', 'rm_worksheet_ids.is_complete')
    def _compute_worksheet_complete(self):
        """Check if all worksheets are complete"""
        for task in self:
            if task.rm_worksheet_ids:
                task.worksheet_complete = all(ws.is_complete for ws in task.rm_worksheet_ids)
            else:
                task.worksheet_complete = False

    @api.depends('stage_id')
    def _compute_service_complete(self):
        """Compute if service is complete based on stage"""
        for task in self:
            # In Odoo 18, project.task.type doesn't provide `is_closed` by default.
            # Use the `fold` attribute (True when a stage is folded/considered done) as a proxy.
            # Fallback to False if stage is not set.
            stage = task.stage_id
            task.service_complete = bool(getattr(stage, 'fold', False)) if stage else False

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_create_worksheet(self, template_id):
        """Create worksheet instance from template"""
        self.ensure_one()
        template = self.env['fsm.worksheet.template'].browse(template_id)
        if not template:
            raise UserError(_("Worksheet template not found"))

        worksheet = self.env['fsm.worksheet.instance'].create({
            'task_id': self.id,
            'template_id': template.id,
        })
        return worksheet

    def action_view_worksheets(self):
        """Open worksheets for this task"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Worksheets'),
            'res_model': 'fsm.worksheet.instance',
            'view_mode': 'tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id},
        }

    def action_generate_destruction_certificate(self):
        """Generate destruction certificate for completed service"""
        self.ensure_one()
        if not self.service_complete:
            raise UserError(_("Cannot generate certificate for incomplete service"))

        # Get weight from worksheet if available
        weight = self.weight_processed
        if not weight and self.rm_worksheet_ids:
            for worksheet in self.rm_worksheet_ids:
                if worksheet.weight_recorded:
                    weight = worksheet.weight_recorded
                    break

        # Certificate generation logic will be implemented in destruction certificate model
        certificate_vals = {
            'fsm_task_id': self.id,
            'partner_id': self.partner_id.id,
            'destruction_date': fields.Date.today(),
            'destruction_type': self.destruction_type,
            'weight_processed': weight,
        }

        # Only add shredding_team_id if field exists
        if hasattr(self, 'shredding_team_id') and self.shredding_team_id:
            certificate_vals['shredding_team_id'] = self.shredding_team_id.id

        certificate = self.env['destruction.certificate'].create(certificate_vals)
        self.destruction_certificate_id = certificate.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Destruction Certificate'),
            'res_model': 'destruction.certificate',
            'res_id': certificate.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def write(self, vals):
        """Auto-complete work orders when FSM task is done"""
        res = super().write(vals)
        
        # If task stage changed to done/closed
        if 'stage_id' in vals:
            for task in self:
                if task.service_complete and task.worksheet_complete:
                    # Auto-complete linked work orders
                    if task.retrieval_work_order_id and task.retrieval_work_order_id.state != 'completed':
                        task.retrieval_work_order_id.action_complete()
                    
                    if task.destruction_work_order_id and task.destruction_work_order_id.state != 'completed':
                        task.destruction_work_order_id.action_complete()
                    
                    if task.shredding_work_order_id and task.shredding_work_order_id.state != 'completed':
                        task.shredding_work_order_id.write({'state': 'completed'})
        
        return res
