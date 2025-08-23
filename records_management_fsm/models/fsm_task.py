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
    destruction_type = fields.Selection([
        ('on_site', 'On-Site Shredding'),
        ('off_site', 'Off-Site Destruction'),
        ('media_destruction', 'Media Destruction'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('specialized', 'Specialized Destruction')
    ], string="Destruction Type")

    # Weight tracking
    weight_processed = fields.Float(
        string="Weight Processed (kg)",
        help="Total weight of materials processed"
    )

    # Certificate generation
    destruction_certificate_id = fields.Many2one(
        'destruction.certificate',
        string="Destruction Certificate",
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

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends('stage_id')
    def _compute_service_complete(self):
        """Compute if service is complete based on stage"""
        for task in self:
            task.service_complete = task.stage_id.is_closed if task.stage_id else False

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_generate_destruction_certificate(self):
        """Generate destruction certificate for completed service"""
        self.ensure_one()
        if not self.service_complete:
            raise UserError(_("Cannot generate certificate for incomplete service"))

        # Certificate generation logic will be implemented in destruction certificate model
        certificate_vals = {
            'fsm_task_id': self.id,
            'partner_id': self.partner_id.id,
            'destruction_date': fields.Date.today(),
            'destruction_type': self.destruction_type,
            'weight_processed': self.weight_processed,
            'shredding_team_id': self.shredding_team_id.id,
        }

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
