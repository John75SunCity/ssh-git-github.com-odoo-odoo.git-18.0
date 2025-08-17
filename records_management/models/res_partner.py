# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
    class ResPartner(models.Model):
    _name = "res.partner"
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "res.partner"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'ResPartner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Core fields"
    name = fields.Char(string='Name', required=True, tracking=True, index=True)""
    active = fields.Boolean(string='Active', default=True)""
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)""
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)""
""
    # State management""
    state = fields.Selection([""
        ('draft', 'Draft'),""
        ('confirmed', 'Confirmed'),""
        ('done', 'Done'),""
        ('cancelled', 'Cancelled'),""
    ], string='Status', default='draft', tracking=True)""
""
    # Dates""
    create_date = fields.Datetime(string='Created On', readonly=True)""
    write_date = fields.Datetime(string='Last Updated', readonly=True)""
""
    # Basic methods""
    def action_confirm(self):""
        """Confirm the record"""
    """
        """Mark as done"""
    """"
        """Cancel the record"""
"""
""""