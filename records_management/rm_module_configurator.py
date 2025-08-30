from odoo import _, api, fields, models


class RmModuleConfigurator(models.Model):
    """Central configuration model for Records Management module toggles.

    This model provides feature enable/disable switches and visibility controls
    for various module components, ensuring configurable behavior across the system.
    """

    _name = "rm.module.configurator"
    _description = "Records Management Module Configurator"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Feature Toggle Fields
    enable_portal_features = fields.Boolean(
        string="Enable Portal Features",
        default=True,
        help="Toggle to enable/disable customer portal functionality",
    )
    enable_mobile_dashboard = fields.Boolean(
        string="Enable Mobile Dashboard",
        default=True,
        help="Toggle to enable/disable mobile dashboard widgets",
    )
    enable_billing_system = fields.Boolean(
        string="Enable Billing System",
        default=True,
        help="Toggle to enable/disable billing and invoicing features",
    )
    enable_naid_compliance = fields.Boolean(
        string="Enable NAID Compliance",
        default=True,
        help="Toggle to enable/disable NAID AAA compliance features",
    )
    enable_chain_of_custody = fields.Boolean(
        string="Enable Chain of Custody",
        default=True,
        help="Toggle to enable/disable chain of custody tracking",
    )
    enable_portal_requests = fields.Boolean(
        string="Enable Portal Requests",
        default=True,
        help="Toggle to enable/disable customer request submissions",
    )

    """Additional Configuration Fields (expand as needed)."""
    default_retention_years = fields.Integer(
        string="Default Retention Years",
        default=7,
        help="Default retention period in years for records",
    )
    enable_audit_logging = fields.Boolean(
        string="Enable Audit Logging",
        default=True,
        help="Toggle to enable/disable comprehensive audit trails",
    )

    @api.model
    def get_singleton_config(self):
        """Ensure only one configuration record exists and return it."""
        config = self.env["rm.module.configurator"].search([], limit=1)
        if not config:
            config = self.env["rm.module.configurator"].create({})
        return config

    @api.model
    def get_config_value(self, key):
        """
        Helper method to retrieve configuration values.

        Returns the value of the given key if it exists on the configuration record,
        otherwise returns False.
        """
        config = self.get_singleton_config()
        return getattr(config, key, False)

    @api.model
    def set_config_value(self, key, value):
        """Helper method to set configuration values; creates a new configuration record if none exists."""
        config = self.get_singleton_config()
        setattr(config, key, value)
        config.message_post(body=_("Configuration updated: %s set to %s", key, value))
