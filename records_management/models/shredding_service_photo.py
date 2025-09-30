from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShreddingServicePhoto(models.Model):
    _name = 'shredding.service.photo'
    _description = 'Shredding Service Photo Documentation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'shredding_service_id, sequence, photo_type'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", compute='_compute_name', store=True, readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # ============================================================================
    # RELATIONSHIP & PHOTO DETAILS
    # ============================================================================
    shredding_service_id = fields.Many2one(
        'project.task',
        string="Shredding Service",
        required=True,
        ondelete='cascade',
        help="The shredding service this photo is associated with."
    )
    photo_type = fields.Selection([
        ('before', 'Before Destruction'),
        ('after', 'After Destruction'),
        ('equipment', 'Equipment Used'),
        ('process', 'During Process'),
        ('other', 'Other')
    ], string="Photo Type", required=True, default='before', tracking=True)

    photo_data = fields.Image(string="Photo", required=True, max_width=1920, max_height=1080)
    photo_date = fields.Datetime(string="Photo Date", default=fields.Datetime.now, required=True, readonly=True)

    # ============================================================================
    # WITNESS & VERIFICATION
    # ============================================================================
    witness_name = fields.Char(string="Witness Name", tracking=True)
    witness_signature = fields.Binary(string="Witness Signature", attachment=True)

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('shredding_service_id.name', 'photo_type')
    def _compute_name(self):
        for record in self:
            if record.shredding_service_id and record.photo_type:
                record.name = _("Photo for %s (%s)") % (
                    record.shredding_service_id.name,
                    dict(record._fields['photo_type'].selection).get(record.photo_type)
                )
            else:
                record.name = _("New Photo")

    @api.constrains('shredding_service_id')
    def _check_shredding_service(self):
        for record in self:
            if not record.shredding_service_id:
                raise ValidationError(_("A photo must be linked to a shredding service."))
