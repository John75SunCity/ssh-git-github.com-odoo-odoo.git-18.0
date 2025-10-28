from odoo import models
from odoo.osv import expression


class IrRule(models.Model):
    _inherit = "ir.rule"

    def _compute_domain(self, model_name, mode):
        """Allow Records Admin users to bypass restrictive record rules."""
        if self.env.is_superuser():
            return super()._compute_domain(model_name, mode)

        if self.env.user.has_group("records_management.group_records_admin"):
            return expression.TRUE_DOMAIN

        return super()._compute_domain(model_name, mode)
