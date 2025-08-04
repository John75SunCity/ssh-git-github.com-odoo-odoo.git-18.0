# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FieldLabelCustomization(models.Model):
    _name = "field.label.customization"
    _description = "Field Label Customization"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", string="Assigned User", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)
    
    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ], string="Status", default="draft", tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string="Priority", default='medium')

    # ============================================================================
    # CUSTOMIZATION SPECIFICATIONS
    # ============================================================================
    model_name = fields.Char(string="Model Name", required=True)
    field_name = fields.Char(string="Field Name", required=True)
    original_label = fields.Char(string="Original Label")
    custom_label = fields.Char(string="Custom Label", required=True)
    
    # Label Templates and Preferences
    default_label_template = fields.Selection([
        ('standard', 'Standard'),
        ('verbose', 'Verbose'),
        ('abbreviated', 'Abbreviated'),
        ('technical', 'Technical')
    ], string="Label Template", default='standard')
    
    label_language_preference = fields.Selection([
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French')
    ], string="Language", default='en')
    
    label_size_customization = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large')
    ], string="Label Size", default='medium')

    # ============================================================================
    # SCOPE AND APPLICATION
    # ============================================================================
    scope = fields.Selection([
        ('global', 'Global'),
        ('company', 'Company'),
        ('user', 'User Specific'),
        ('department', 'Department')
    ], string="Scope", default='company')
    
    department_ids = fields.Many2many("hr.department", string="Departments")
    user_ids = fields.Many2many("res.users", string="Specific Users")
    
    # ============================================================================
    # COMPLIANCE AND INDUSTRY
    # ============================================================================
    industry_type = fields.Selection([
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('legal', 'Legal'),
        ('manufacturing', 'Manufacturing'),
        ('education', 'Education'),
        ('government', 'Government'),
        ('generic', 'Generic')
    ], string="Industry Type", default='generic')
    
    compliance_framework = fields.Selection([
        ('hipaa', 'HIPAA'),
        ('gdpr', 'GDPR'),
        ('sox', 'SOX'),
        ('iso27001', 'ISO 27001'),
        ('naid', 'NAID AAA'),
        ('custom', 'Custom')
    ], string="Compliance Framework")
    
    security_classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string="Security Classification", default='internal')

    # ============================================================================
    # DISPLAY AND FORMATTING
    # ============================================================================
    font_size_preference = fields.Selection([
        ('small', 'Small'),
        ('normal', 'Normal'),
        ('large', 'Large'),
        ('x-large', 'Extra Large')
    ], string="Font Size", default='normal')
    
    help_text = fields.Text(string="Help Text")
    placeholder_text = fields.Char(string="Placeholder Text")
    tooltip_text = fields.Text(string="Tooltip Text")

    # ============================================================================
    # DATES AND TIMESTAMPS
    # ============================================================================
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")
    effective_date = fields.Date(string="Effective Date")
    expiry_date = fields.Date(string="Expiry Date")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    popularity_score = fields.Float(string="Popularity Score", compute="_compute_popularity_score")
    scope_display = fields.Char(string="Scope Display", compute="_compute_scope_display")
    customized_label_count = fields.Integer(string="Customized Labels", compute="_compute_customized_label_count")

    # ============================================================================
    # DESCRIPTIVE FIELDS
    # ============================================================================
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")
    special_instructions = fields.Text(string="Special Instructions")

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('name', 'model_name', 'field_name')
    def _compute_display_name(self):
        """Compute display name from components"""
        for record in self:
            if record.model_name and record.field_name:
                record.display_name = f"{record.name} ({record.model_name}.{record.field_name})"
            else:
                record.display_name = record.name or ''

    def _compute_popularity_score(self):
        """Calculate popularity based on usage"""
        for record in self:
            # Simplified popularity calculation
            base_score = len(record.user_ids) * 10
            if record.scope == 'global':
                base_score += 100
            elif record.scope == 'company':
                base_score += 50
            record.popularity_score = base_score

    @api.depends('scope', 'department_ids', 'user_ids')
    def _compute_scope_display(self):
        """Display scope information"""
        for record in self:
            if record.scope == 'global':
                record.scope_display = 'Global'
            elif record.scope == 'company':
                record.scope_display = f'Company: {record.company_id.name}'
            elif record.scope == 'department':
                dept_names = record.department_ids.mapped('name')
                record.scope_display = f'Departments: {", ".join(dept_names)}'
            elif record.scope == 'user':
                user_names = record.user_ids.mapped('name')
                record.scope_display = f'Users: {", ".join(user_names[:3])}'
            else:
                record.scope_display = 'Not Specified'

    def _compute_customized_label_count(self):
        """Count customized labels"""
        for record in self:
            # This would typically count related customizations
            record.customized_label_count = 1 if record.custom_label else 0

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the customization"""
        self.ensure_one()
        self.state = 'active'
        self.date_modified = fields.Datetime.now()
        self.message_post(body="Label customization activated")

    def action_deactivate(self):
        """Deactivate the customization"""
        self.ensure_one()
        self.state = 'inactive'
        self.date_modified = fields.Datetime.now()
        self.message_post(body="Label customization deactivated")

    def action_archive(self):
        """Archive the customization"""
        self.ensure_one()
        self.state = 'archived'
        self.active = False
        self.message_post(body="Label customization archived")

    def action_apply_customization(self):
        """Apply the label customization"""
        self.ensure_one()
        if not self.custom_label:
            raise UserError("Custom label is required")
        # Implementation would apply the customization
        self.message_post(body=f"Applied customization: {self.custom_label}")

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('model_name', 'field_name')
    def _check_model_field_exists(self):
        """Validate that model and field exist"""
        for record in self:
            if record.model_name and record.field_name:
                if record.model_name not in self.env:
                    raise ValidationError(f"Model {record.model_name} does not exist")

    @api.constrains('effective_date', 'expiry_date')
    def _check_date_sequence(self):
        """Validate date sequence"""
        for record in self:
            if record.effective_date and record.expiry_date:
                if record.effective_date > record.expiry_date:
                    raise ValidationError("Effective date cannot be after expiry date")

    @api.constrains('custom_label')
    def _check_custom_label(self):
        """Validate custom label"""
        for record in self:
            if record.custom_label and len(record.custom_label) > 100:
                raise ValidationError("Custom label cannot exceed 100 characters")

    # ============================================================================
    # ODOO FRAMEWORK INTEGRATION
    # ============================================================================
    @api.model
    def create(self, vals):
        """Override create for initialization"""
        if 'date_modified' not in vals:
            vals['date_modified'] = fields.Datetime.now()
        return super().create(vals)

    def write(self, vals):
        """Override write for modification tracking"""
        vals['date_modified'] = fields.Datetime.now()
        result = super().write(vals)
        for record in self:
            if 'state' in vals:
                record.message_post(body=f"State changed to {record.state}")
        return result

    def unlink(self):
        """Override unlink with validation"""
        for record in self:
            if record.state == 'active':
                raise UserError(f"Cannot delete active customization: {record.name}")
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.model_name and record.field_name:
                name += f" ({record.model_name}.{record.field_name})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search capabilities"""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|',
                     ('name', operator, name),
                     ('model_name', operator, name),
                     ('field_name', operator, name),
                     ('custom_label', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
