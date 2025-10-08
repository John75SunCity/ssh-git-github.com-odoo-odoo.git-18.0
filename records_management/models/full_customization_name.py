from odoo import _, api, fields, models

class FullCustomizationName(models.Model):
    _name = 'full.customization.name'
    _description = 'Full Customization Name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, id desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, help="Name of the customization configuration")
    description = fields.Text(
        string='Description',
        help="Detailed description of the customization"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to disable this customization without deleting it"
    )

    # System Fields
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Customization Owner",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this customization",
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('name', 'description')
    def _compute_display_name(self):
        """Compute a user-friendly display name"""
        for record in self:
            if record.description:
                record.display_name = "%s - %s" % (record.name, record.description[:50])
            else:
                record.display_name = record.name

    # Deprecated name_get: Odoo 19 uses computed display_name

    @api.constrains('name')
    def _check_name_unique(self):
        """Ensure customization names are unique per company"""
        for record in self:
            domain = [
                ('name', '=', record.name),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ]
            if self.search_count(domain) > 0:
                raise ValueError(_("A customization with this name already exists in the company"))

    def action_duplicate(self):
        """Create a copy of this customization"""
        self.ensure_one()
        copy_vals = {
            "name": _("%s (Copy)") % self.name,
            "description": self.description,
            "user_id": self.env.user.id,
        }
        new_record = self.copy(copy_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customization Copy'),
            'res_model': self._name,
            'res_id': new_record.id,
            'view_mode': 'form',
            'target': 'current',
        }
