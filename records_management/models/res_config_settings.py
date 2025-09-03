from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ============================================================================
    # FIELDS - These fields act as an interface to rm.module.configurator
    # ============================================================================
    # Example for a boolean toggle (Feature Toggle)
    naid_compliance_enabled = fields.Boolean(
        string="Enable NAID Compliance",
        config_parameter='records_management.naid_compliance_enabled',
        help="Enables full NAID AAA compliance tracking and reporting."
    )

    # Example for a parameter (System Parameter)
    naid_audit_retention_days = fields.Integer(
        string="NAID Audit Retention (Days)",
        config_parameter='records_management.naid_audit_retention_days',
        help="Number of days to retain NAID audit logs."
    )

    # Add other fields here following the same pattern...
    # ...

    # ============================================================================
    # METHODS - Bridge between res.config.settings and rm.module.configurator
    # ============================================================================
    @api.model
    def get_values(self):
        """
        Reads values from rm.module.configurator and ir.config_parameter
        to display on the settings page.
        """
        res = super(ResConfigSettings, self).get_values()
        Config = self.env['rm.module.configurator']

        # Get values from the custom configurator
        res.update({
            'naid_compliance_enabled': Config.get_config_parameter('naid.compliance.enabled', default=False),
            'naid_audit_retention_days': Config.get_config_parameter('naid.audit.retention_days', default=3650),
        })
        return res

    def set_values(self):
        """
        Takes values from the settings page and saves them to the
        rm.module.configurator, creating records if they don't exist.
        """
        super(ResConfigSettings, self).set_values()
        Config = self.env['rm.module.configurator']

        # Use the new set_config_parameter method for better reusability
        Config.set_config_parameter(
            'naid.compliance.enabled',
            self.naid_compliance_enabled,
            config_type='feature_toggle',
            name='Enable NAID Compliance',
            category='compliance'
        )

        Config.set_config_parameter(
            'naid.audit.retention_days',
            self.naid_audit_retention_days,
            config_type='parameter',
            name='NAID Audit Retention (Days)',
            category='compliance'
        )
                'value_boolean': self.naid_compliance_enabled,
                'category': 'compliance',
            })

        # Update or create the retention days parameter
        retention_param = Config.search([('config_key', '=', 'naid.audit.retention_days')], limit=1)
        if retention_param:
            retention_param.value_number = self.naid_audit_retention_days
        else:
            Config.create({
                'name': 'NAID Audit Retention (Days)',
                'config_key': 'naid.audit.retention_days',
                'config_type': 'parameter',
                'value_number': self.naid_audit_retention_days,
                'category': 'compliance',
            })
