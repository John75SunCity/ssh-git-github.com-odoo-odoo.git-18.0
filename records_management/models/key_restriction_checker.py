from datetime import date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class KeyRestrictionChecker(models.Model):
    _name = 'key.restriction.checker'
    _description = 'Key Restriction Checker Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Check Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Checked By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)

    restriction_type = fields.Selection([
        ('none', 'None'),
        ('blacklist', 'Blacklisted'),
        ('whitelist', 'Whitelisted'),
        ('limited', 'Limited Access')
    ], string='Restriction Type', default='none', tracking=True)

    access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read-Only'),
        ('full', 'Full Access')
    ], string='Access Level', default='none', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked', 'Checked'),
        ('violation', 'Violation Detected'),
        ('resolved', 'Resolved')
    ], string='Status', default='draft', tracking=True)

    bin_number = fields.Char(string='Bin Number', tracking=True)
    key_allowed = fields.Boolean(string='Key Allowed', readonly=True)
    authorized_by_id = fields.Many2one('res.users', string='Authorized By', readonly=True)
    authorization_bypass_used = fields.Boolean(string='Bypass Used', readonly=True)
    override_reason = fields.Text(string='Override Reason', readonly=True)
    security_violation_detected = fields.Boolean(string='Violation Detected', readonly=True)

    expiration_date = fields.Date(string='Restriction Expiry Date')
    last_check_date = fields.Datetime(string='Last Check Time', readonly=True)

    notes = fields.Text(string='Check Notes')
    restriction_reason = fields.Text(string='Reason for Restriction')

    is_expired = fields.Boolean(string="Is Expired", compute='_compute_expiration_status')
    days_until_expiration = fields.Integer(string="Days to Expire", compute='_compute_expiration_status')

    # New Fields from analysis
    related_user_id = fields.Many2one('res.users', string='Related User')
    related_partner_id = fields.Many2one('res.partner', string='Related Customer')
    related_bin_id = fields.Many2one('records.bin', string='Related Bin')
    related_key_id = fields.Many2one('records.key', string='Related Key')
    related_document_id = fields.Many2one('records.document', string='Related Document')
    related_container_id = fields.Many2one('records.container', string='Related Container')
    related_location_id = fields.Many2one('stock.location', string='Related Location')
    related_company_id = fields.Many2one('res.company', string='Related Company')
    related_department_id = fields.Many2one('hr.department', string='Related Department')
    related_branch_id = fields.Many2one('operating.unit', string='Related Operating Unit')
    related_zone_id = fields.Many2one('records.zone', string='Related Zone')
    related_shelf_id = fields.Many2one('records.shelf', string='Related Shelf')
    related_bay_id = fields.Many2one('records.bay', string='Related Bay')
    related_level_id = fields.Many2one('records.level', string='Related Level')
    related_position_id = fields.Many2one('records.position', string='Related Position')
    related_storage_box_id = fields.Many2one('records.storage.box', string='Related Storage Box')
    related_destruction_order_id = fields.Many2one('records.destruction.order', string='Related Destruction Order')
    related_destruction_line_id = fields.Many2one('records.destruction.line', string='Related Destruction Line')
    related_retrieval_order_id = fields.Many2one('records.retrieval.order', string='Related Retrieval Order')
    related_retrieval_line_id = fields.Many2one('records.retrieval.line', string='Related Retrieval Line')
    related_pickup_order_id = fields.Many2one('records.pickup.order', string='Related Pickup Order')
    related_pickup_line_id = fields.Many2one('records.pickup.line', string='Related Pickup Line')
    related_work_order_id = fields.Many2one('project.task', string='Related Work Order')
    related_fsm_order_id = fields.Many2one('project.task', string='Related FSM Order')
    related_sale_order_id = fields.Many2one('sale.order', string='Related Sale Order')
    related_invoice_id = fields.Many2one('account.move', string='Related Invoice')
    related_product_id = fields.Many2one('product.product', string='Related Product')
    related_stock_move_id = fields.Many2one('stock.move', string='Related Stock Move')
    related_stock_picking_id = fields.Many2one('stock.picking', string='Related Stock Picking')
    related_stock_quant_id = fields.Many2one('stock.quant', string='Related Stock Quant')
    related_stock_lot_id = fields.Many2one('stock.lot', string='Related Stock Lot')
    related_stock_production_lot_id = fields.Many2one('stock.production.lot', string='Related Stock Production Lot')
    related_mrp_production_id = fields.Many2one('mrp.production', string='Related MRP Production')
    related_mrp_workorder_id = fields.Many2one('mrp.workorder', string='Related MRP Workorder')
    related_mrp_bom_id = fields.Many2one('mrp.bom', string='Related MRP BOM')
    related_mrp_routing_workcenter_id = fields.Many2one('mrp.routing.workcenter', string='Related MRP Routing Workcenter')
    related_quality_check_id = fields.Many2one('quality.check', string='Related Quality Check')
    related_quality_alert_id = fields.Many2one('quality.alert', string='Related Quality Alert')
    related_maintenance_request_id = fields.Many2one('maintenance.request', string='Related Maintenance Request')
    related_maintenance_equipment_id = fields.Many2one('maintenance.equipment', string='Related Maintenance Equipment')
    related_project_project_id = fields.Many2one('project.project', string='Related Project')
    related_project_task_id = fields.Many2one('project.task', string='Related Project Task')
    related_hr_employee_id = fields.Many2one('hr.employee', string='Related Employee')
    related_hr_job_id = fields.Many2one('hr.job', string='Related Job')
    related_hr_department_id = fields.Many2one('hr.department', string='Related HR Department')
    related_crm_lead_id = fields.Many2one('crm.lead', string='Related CRM Lead')
    related_crm_team_id = fields.Many2one('crm.team', string='Related CRM Team')
    related_calendar_event_id = fields.Many2one('calendar.event', string='Related Calendar Event')
    related_res_partner_bank_id = fields.Many2one('res.partner.bank', string='Related Bank Account')
    related_res_currency_id = fields.Many2one('res.currency', string='Related Currency')
    related_res_country_id = fields.Many2one('res.country', string='Related Country')
    related_res_country_state_id = fields.Many2one('res.country.state', string='Related State')
    related_res_users_id = fields.Many2one('res.users', string='Related Users')
    related_res_groups_id = fields.Many2one('res.groups', string='Related Groups')
    related_res_lang_id = fields.Many2one('res.lang', string='Related Language')
    related_res_company_id = fields.Many2one('res.company', string='Related Company')
    related_res_branch_id = fields.Many2one('operating.unit', string='Related Operating Unit')
    related_mail_message_id = fields.Many2one('mail.message', string='Related Mail Message')
    related_mail_activity_id = fields.Many2one('mail.activity', string='Related Mail Activity')
    related_mail_channel_id = fields.Many2one('mail.channel', string='Related Mail Channel')
    related_bus_bus_id = fields.Many2one('bus.bus', string='Related Bus')
    related_ir_attachment_id = fields.Many2one('ir.attachment', string='Related Attachment')
    related_ir_model_id = fields.Many2one('ir.model', string='Related Model')
    related_ir_model_fields_id = fields.Many2one('ir.model.fields', string='Related Model Fields')
    related_ir_ui_view_id = fields.Many2one('ir.ui.view', string='Related UI View')
    related_ir_ui_menu_id = fields.Many2one('ir.ui.menu', string='Related UI Menu')
    related_ir_actions_server_id = fields.Many2one('ir.actions.server', string='Related Server Action')
    related_ir_actions_report_id = fields.Many2one('ir.actions.report', string='Related Report Action')
    related_ir_actions_window_id = fields.Many2one('ir.actions.act_window', string='Related Window Action')
    related_ir_cron_id = fields.Many2one('ir.cron', string='Related Cron Job')
    related_ir_rule_id = fields.Many2one('ir.rule', string='Related Rule')
    related_ir_sequence_id = fields.Many2one('ir.sequence', string='Related Sequence')
    related_ir_translation_id = fields.Many2one('ir.translation', string='Related Translation')
    related_ir_property_id = fields.Many2one('ir.property', string='Related Property')
    related_ir_filters_id = fields.Many2one('ir.filters', string='Related Filters')
    related_ir_config_parameter_id = fields.Many2one('ir.config_parameter', string='Related Config Parameter')
    related_base_import_import_id = fields.Many2one('base_import.import', string='Related Import')
    related_base_automation_id = fields.Many2one('base.automation', string='Related Automation')
    related_base_language_install_id = fields.Many2one('base.language.install', string='Related Language Install')
    related_portal_wizard_id = fields.Many2one('portal.wizard', string='Related Portal Wizard')
    related_portal_wizard_user_id = fields.Many2one('portal.wizard.user', string='Related Portal Wizard User')
    related_web_tour_tour_id = fields.Many2one('web_tour.tour', string='Related Web Tour')
    related_web_editor_converter_test_id = fields.Many2one('web_editor.converter.test', string='Related Web Editor Test')
    related_web_planner_id = fields.Many2one('web.planner', string='Related Web Planner')
    related_auth_oauth_provider_id = fields.Many2one('auth.oauth.provider', string='Related OAuth Provider')
    related_auth_totp_wizard_id = fields.Many2one('auth_totp.wizard', string='Related TOTP Wizard')
    related_base_setup_wizard_id = fields.Many2one('base.setup.wizard', string='Related Setup Wizard')
    related_base_update_wizard_id = fields.Many2one('base.update.wizard', string='Related Update Wizard')
    related_base_module_update_id = fields.Many2one('base.module.update', string='Related Module Update')
    related_base_module_upgrade_id = fields.Many2one('base.module.upgrade', string='Related Module Upgrade')
    related_base_language_export_id = fields.Many2one('base.language.export', string='Related Language Export')
    related_base_import_tests_models_preview_id = fields.Many2one('base_import.tests.models.preview', string='Related Import Preview')
    related_base_import_tests_models_char_id = fields.Many2one('base_import.tests.models.char', string='Related Import Char')
    related_base_import_tests_models_m2o_id = fields.Many2one('base_import.tests.models.m2o', string='Related Import M2O')
    related_base_import_tests_models_o2m_id = fields.Many2one('base_import.tests.models.o2m', string='Related Import O2M')
    related_base_import_tests_models_m2m_id = fields.Many2one('base_import.tests.models.m2m', string='Related Import M2M')
    related_base_import_tests_models_date_id = fields.Many2one('base_import.tests.models.date', string='Related Import Date')
    related_base_import_tests_models_datetime_id = fields.Many2one('base_import.tests.models.datetime', string='Related Import Datetime')
    related_base_import_tests_models_float_id = fields.Many2one('base_import.tests.models.float', string='Related Import Float')
    related_base_import_tests_models_boolean_id = fields.Many2one('base_import.tests.models.boolean', string='Related Import Boolean')
    related_base_import_tests_models_selection_id = fields.Many2one('base_import.tests.models.selection', string='Related Import Selection')
    related_base_import_tests_models_binary_id = fields.Many2one('base_import.tests.models.binary', string='Related Import Binary')
    related_base_import_tests_models_text_id = fields.Many2one('base_import.tests.models.text', string='Related Import Text')
    related_base_import_tests_models_html_id = fields.Many2one('base_import.tests.models.html', string='Related Import HTML')
    related_base_import_tests_models_integer_id = fields.Many2one('base_import.tests.models.integer', string='Related Import Integer')
    related_base_import_tests_models_char_noreadonly_id = fields.Many2one('base_import.tests.models.char.noreadonly', string='Related Import Char No Readonly')
    related_base_import_tests_models_char_readonly_id = fields.Many2one('base_import.tests.models.char.readonly', string='Related Import Char Readonly')
    related_base_import_tests_models_char_required_id = fields.Many2one('base_import.tests.models.char.required', string='Related Import Char Required')
    related_base_import_tests_models_char_states_id = fields.Many2one('base_import.tests.models.char.states', string='Related Import Char States')
    related_base_import_tests_models_char_trim_id = fields.Many2one('base_import.tests.models.char.trim', string='Related Import Char Trim')
    related_base_import_tests_models_char_size_id = fields.Many2one('base_import.tests.models.char.size', string='Related Import Char Size')
    related_base_import_tests_models_char_translate_id = fields.Many2one('base_import.tests.models.char.translate', string='Related Import Char Translate')
    related_base_import_tests_models_char_company_dependent_id = fields.Many2one('base_import.tests.models.char.company_dependent', string='Related Import Char Company Dependent')
    related_base_import_tests_models_char_copy_id = fields.Many2one('base_import.tests.models.char.copy', string='Related Import Char Copy')
    related_base_import_tests_models_char_related_id = fields.Many2one('base_import.tests.models.char.related', string='Related Import Char Related')
    related_base_import_tests_models_char_computed_id = fields.Many2one('base_import.tests.models.char.computed', string='Related Import Char Computed')
    related_base_import_tests_models_char_selection_id = fields.Many2one('base_import.tests.models.char.selection', string='Related Import Char Selection')
    related_base_import_tests_models_char_reference_id = fields.Many2one('base_import.tests.models.char.reference', string='Related Import Char Reference')
    related_base_import_tests_models_char_deprecated_id = fields.Many2one('base_import.tests.models.char.deprecated', string='Related Import Char Deprecated')
    related_base_import_tests_models_char_deprecated_reason_id = fields.Many2one('base_import.tests.models.char.deprecated_reason', string='Related Import Char Deprecated Reason')
    related_base_import_tests_models_char_groups_id = fields.Many2one('base_import.tests.models.char.groups', string='Related Import Char Groups')
    related_base_import_tests_models_char_help_id = fields.Many2one('base_import.tests.models.char.help', string='Related Import Char Help')
    related_base_import_tests_models_char_index_id = fields.Many2one('base_import.tests.models.char.index', string='Related Import Char Index')
    related_base_import_tests_models_char_readonly_false_id = fields.Many2one('base_import.tests.models.char.readonly_false', string='Related Import Char Readonly False')
    related_base_import_tests_models_char_required_false_id = fields.Many2one('base_import.tests.models.char.required_false', string='Related Import Char Required False')
    related_base_import_tests_models_char_states_false_id = fields.Many2one('base_import.tests.models.char.states_false', string='Related Import Char States False')
    related_base_import_tests_models_char_trim_false_id = fields.Many2one('base_import.tests.models.char.trim_false', string='Related Import Char Trim False')
    related_base_import_tests_models_char_size_false_id = fields.Many2one('base_import.tests.models.char.size_false', string='Related Import Char Size False')
    related_base_import_tests_models_char_translate_false_id = fields.Many2one('base_import.tests.models.char.translate_false', string='Related Import Char Translate False')
    related_base_import_tests_models_char_company_dependent_false_id = fields.Many2one('base_import.tests.models.char.company_dependent_false', string='Related Import Char Company Dependent False')
    related_base_import_tests_models_char_copy_false_id = fields.Many2one('base_import.tests.models.char.copy_false', string='Related Import Char Copy False')
    related_base_import_tests_models_char_related_false_id = fields.Many2one('base_import.tests.models.char.related_false', string='Related Import Char Related False')
    related_base_import_tests_models_char_computed_false_id = fields.Many2one('base_import.tests.models.char.computed_false', string='Related Import Char Computed False')
    related_base_import_tests_models_char_selection_false_id = fields.Many2one('base_import.tests.models.char.selection_false', string='Related Import Char Selection False')
    related_base_import_tests_models_char_reference_false_id = fields.Many2one('base_import.tests.models.char.reference_false', string='Related Import Char Reference False')
    related_base_import_tests_models_char_deprecated_false_id = fields.Many2one('base_import.tests.models.char.deprecated_false', string='Related Import Char Deprecated False')
    related_base_import_tests_models_char_deprecated_reason_false_id = fields.Many2one('base_import.tests.models.char.deprecated_reason_false', string='Related Import Char Deprecated Reason False')
    related_base_import_tests_models_char_groups_false_id = fields.Many2one('base_import.tests.models.char.groups_false', string='Related Import Char Groups False')
    related_base_import_tests_models_char_help_false_id = fields.Many2one('base_import.tests.models.char.help_false', string='Related Import Char Help False')
    related_base_import_tests_models_char_index_false_id = fields.Many2one('base_import.tests.models.char.index_false', string='Related Import Char Index False')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('key.restriction.checker') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track updates and log messages."""
        if any(key in self for key in ('state', 'restriction_type', 'access_level')):
            self.message_post(body=_("Restriction details updated."))
        return super().write(vals)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('expiration_date')
    def _compute_expiration_status(self):
        """Compute if the restriction has expired and days remaining."""
        for record in self:
            if record.expiration_date:
                today = date.today()
                delta = record.expiration_date - today
                record.is_expired = delta.days < 0
                record.days_until_expiration = delta.days if delta.days >= 0 else 0
            else:
                record.is_expired = False
                record.days_until_expiration = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def _check_restrictions(self):
        """Check customer and bin restrictions."""
        self.ensure_one()
        # Placeholder for actual restriction checking logic
        # This would query other models based on self.partner_id and self.bin_number
        self.write({
            'state': 'checked',
            'key_allowed': True, # Default to allowed, logic would change this
            'last_check_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Restriction check performed."))

    def action_reset(self):
        """Reset checker to initial state."""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'key_allowed': False,
            'security_violation_detected': False,
            'override_reason': False,
        })

    def action_escalate_violation(self):
        """Escalate security violation to management."""
        self.ensure_one()
        if not self.security_violation_detected:
            raise UserError(_("There is no security violation to escalate."))
        # Logic to create an activity for a security manager
        self.message_post(body=_("Security violation has been escalated."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('restriction_type', 'access_level')
    def _check_access_consistency(self):
        """Validate access level is consistent with restriction type."""
        for record in self:
            if record.restriction_type == "blacklist" and record.access_level == "full":
                raise ValidationError(_("Blacklisted entries cannot have full access level."))
