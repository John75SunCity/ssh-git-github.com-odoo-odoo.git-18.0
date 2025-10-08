try:  # pragma: no cover - fallback if dateutil stub warning persists
    from dateutil.relativedelta import relativedelta  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    # Minimal fallback that only supports months addition on date objects
    class relativedelta:  # type: ignore
        def __init__(self, months=0):
            self.months = months

        def __radd__(self, other):  # date + relativedelta
            if hasattr(other, 'month') and hasattr(other, 'year'):
                # naive month addition
                month = other.month - 1 + self.months
                year = other.year + month // 12
                month = month % 12 + 1
                # clamp day
                day = min(getattr(other, 'day', 1), 28)
                from datetime import date as _date
                return _date(year, month, day)
            return other

from odoo import models, fields, api, _
# NOTE: Avoid _lt (lazy translation) here because during model table creation
# PostgreSQL COMMENT parameters received a lazy object (LazyGettext) which
# psycopg2 could not adapt ("can't adapt type 'LazyGettext'"). Using the
# immediate translation function _() returns a plain string and prevents the
# registry load failure.

class NaidOperatorCertification(models.Model):
    _name = 'naid.operator.certification'
    _description = 'NAID Operator Certification'
    _inherit = ['hr.employee', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']  # Inherit from hr.employee for employee data integration
    _order = 'name'

    # ------------------------------------------------------------------
    # FIELD LABEL DISAMBIGUATION
    # ------------------------------------------------------------------
    # hr.employee provides employee_token (label "Security Token") and
    # portal.mixin provides access_token (label "Security Token"). Both
    # inherited simultaneously here caused the runtime warning about
    # duplicate labels. We override their string labels to make them
    # semantically distinct while preserving underlying behavior.
    # Use plain strings (no _()) to avoid import-time translation context warnings; field labels still extractable via pot init
    employee_token = fields.Char(string='Employee Security Token')  # override label only
    access_token = fields.Char(string='Portal Access Token')  # override label only

    # Core certification fields
    certification_number = fields.Char(string='Certification Number', required=True, tracking=True, default=lambda self: self._generate_certification_number())
    certification_date = fields.Date(string='Certification Date', default=fields.Date.context_today, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True, help='Date when certification expires')
    status = fields.Selection([
        ('pending', 'Pending Training'),
        ('in_progress', 'Training in Progress'),
        ('certified', 'Certified'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked')
    ], string='Record Status', default='pending', tracking=True)  # Disambiguated from any other certification status fields

    # Training and verification fields (requires website_slides module)
    # Explicit relation table + columns for validator compliance (auto naming avoided intentionally)
    required_trainings_ids = fields.Many2many(
        'slide.channel',
        'naid_cert_required_training_rel',  # relation table
        'certification_id',  # current model FK
        'training_id',  # slide.channel FK
        string='Required Trainings',
        help='Trainings the operator must complete (from learning module if installed)'
    )
    completed_trainings_ids = fields.Many2many('slide.channel', 'naid_cert_training_rel', 'certification_id', 'training_id', string='Completed Trainings', help='Trainings successfully completed')
    training_verified = fields.Boolean(string='Training Verified', default=False, tracking=True, help='Indicates if all required trainings are completed and verified')
    verified_by_id = fields.Many2one(comodel_name='res.users', string='Verified By', tracking=True, help='User who verified the training completion')
    verification_date = fields.Date(string='Verification Date', tracking=True)

    # Recurring training and refreshers
    refresher_training_required = fields.Boolean(string='Refresher Training Required', default=True, help='Whether this certification requires periodic refresher training')
    refresher_interval_months = fields.Integer(string='Refresher Interval (Months)', default=12, help='How often refresher training is required')
    last_refresher_date = fields.Date(string='Last Refresher Date', tracking=True)
    next_refresher_date = fields.Date(string='Next Refresher Date', compute='_compute_next_refresher', store=True)
    refresher_overdue = fields.Boolean(string='Refresher Overdue', compute='_compute_refresher_status', store=True)

    # Training schedule and tracking
    training_schedule_ids = fields.One2many('naid.training.schedule', 'certification_id', string='Training Schedule')
    training_progress = fields.Float(string='Training Progress (%)', compute='_compute_training_progress', store=True)

    # Relationships to other modules
    destruction_certificate_ids = fields.One2many('destruction.certificate', 'operator_certification_id', string='Destruction Certificates')
    fsm_order_ids = fields.One2many('project.task', 'operator_certification_id', string='FSM Tasks', domain=[('is_fsm', '=', True)])
    service_request_ids = fields.One2many('portal.request', 'assigned_operator_id', string='Service Requests')

    # Customer portal visibility
    portal_visible = fields.Boolean(string='Visible to Customers', default=True, help='Whether this certification info is visible to customers in portal')

    category_ids = fields.Many2many(
        'hr.employee.category', 'naid_cert_category_rel',
        'cert_id', 'category_id', string='NAID Tags')

    # Additional details
    notes = fields.Text(string='Notes', help='Additional notes on certification or training')
    attachment_ids = fields.Many2many('ir.attachment', 'naid_operator_cert_attachment_rel', 'certification_id', 'attachment_id', string='Supporting Documents', help='Certificates, training records, etc.')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    # Explicit override of hr.employee's bank_account_ids to ensure a unique relation table.
    # Odoo 19 registry error reported a collision: Many2many fields share the same table/columns.
    # We provide a distinct relation table name to avoid conflict with hr.employee's default.
    bank_account_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        relation='naid_operator_cert_bank_rel',  # unique relation table
        column1='cert_id',  # FK to this certification model
        column2='bank_id',  # FK to res.partner.bank
        string='Bank Accounts',
        help='Bank accounts associated specifically with this operator certification record'
    )

    # Explicit override of hr.employee's goals_ids to ensure a unique relation table.
    # Similar registry collision observed for goals_ids (performance/gamification goals) on Odoo 19.
    # We provide a distinct relation table and column names to isolate this model's linkage.
    goals_ids = fields.Many2many(
        comodel_name='gamification.goal',
        relation='naid_operator_cert_goal_rel',  # unique relation table distinct from hr.employee default
        column1='cert_id',  # FK to this certification model
        column2='goal_id',  # FK to gamification.goal
        string='Performance Goals',
        help='Gamification / performance goals tracked specifically for this operator certification'
    )

    # ------------------------------------------------------------------
    # VIEW-REFERENCED FIELDS (Added to satisfy missing field audit)
    # ------------------------------------------------------------------
    # 'name' is used in views explicitly; hr.employee inheritance already provides name but we
    # expose an explicit related for clarity and to ensure store behavior for this model's table.
    name = fields.Char(string='Operator Name', related='display_name', store=False)
    # certificate_number (alias of certification_number for legacy view references)
    certificate_number = fields.Char(string='Certificate Number', help='Legacy alias referencing certification number')
    certification_type = fields.Selection([
        ('initial', 'Initial Certification'),
        ('refresher', 'Refresher'),
        ('specialized', 'Specialized Equipment'),
        ('safety', 'Safety Compliance')
    ], string='Certification Type', help='Type/category of certification')
    completed_date = fields.Date(string='Completed Date', help='Date when all training requirements were completed')
    instructor_id = fields.Many2one(comodel_name='res.users', string='Instructor', help='Primary instructor or trainer responsible')
    issue_date = fields.Date(string='Issue Date', help='Official issuance date of certificate (may differ from completion)')
    issuing_authority = fields.Char(string='Issuing Authority', help='Organization or authority issuing the certification')
    scheduled_date = fields.Date(string='Scheduled Date', help='Initial scheduled date for training/certification')
    scope_of_certification = fields.Text(string='Scope of Certification', help='Defines what operational scope this certification covers')
    training_id = fields.Many2one(comodel_name='slide.channel', string='Primary Training', help='Primary training channel/course this certification is based on')
    operator_id = fields.Many2one(comodel_name='hr.employee', string='Operator (Employee)', help='Explicit operator reference when linking externally')

    @api.model
    def _generate_certification_number(self):
        """Generate a unique certification number"""
        return self.env['ir.sequence'].next_by_code('naid.operator.certification') or 'NAID-CERT-001'

    @api.depends('completed_trainings_ids', 'required_trainings_ids')
    def _compute_training_verified(self):
        """Automatically verify if all required trainings are completed"""
        for record in self:
            if record.required_trainings_ids and set(record.completed_trainings_ids.ids) == set(record.required_trainings_ids.ids):
                record.training_verified = True
            else:
                record.training_verified = False

    @api.depends('certification_date', 'refresher_interval_months', 'last_refresher_date')
    def _compute_next_refresher(self):
        """Compute next refresher training date"""
        for record in self:
            if record.refresher_training_required:
                base_date = record.last_refresher_date or record.certification_date
                if base_date:
                    record.next_refresher_date = base_date + relativedelta(months=record.refresher_interval_months)
                else:
                    record.next_refresher_date = False
            else:
                record.next_refresher_date = False

    @api.depends('next_refresher_date')
    def _compute_refresher_status(self):
        """Compute if refresher training is overdue"""
        today = fields.Date.context_today(self)
        for record in self:
            record.refresher_overdue = record.next_refresher_date and record.next_refresher_date < today

    @api.depends('completed_trainings_ids', 'required_trainings_ids')
    def _compute_training_progress(self):
        """Compute training completion progress percentage"""
        for record in self:
            if record.required_trainings_ids:
                completed_count = len(record.completed_trainings_ids)
                required_count = len(record.required_trainings_ids)
                record.training_progress = (completed_count / required_count) * 100
            else:
                record.training_progress = 0.0

    def action_verify_training(self):
        """Verify training completion and update status"""
        self.ensure_one()
        if self.training_verified:
            self.status = 'certified'
            self.verified_by_id = self.env.user
            self.verification_date = fields.Date.context_today(self)
            self.last_refresher_date = fields.Date.context_today(self)
            self.message_post(body=f"Operator {self.name} has been certified after completing all required trainings.")
        else:
            self.status = 'pending'

    def action_schedule_refresher(self):
        """Schedule refresher training"""
        self.ensure_one()
        if self.refresher_training_required:
            # Reset training progress for refresher
            self.completed_trainings_ids = [(5, 0, 0)]  # Clear completed trainings
            self.training_verified = False
            self.status = 'pending'
            self.last_refresher_date = fields.Date.context_today(self)
            self.message_post(body=f"Refresher training scheduled for operator {self.name}.")

    def _check_expiry(self):
        """Check and update certification expiry status"""
        today = fields.Date.context_today(self)
        expired_records = self.search([
            ('expiry_date', '<', today),
            ('status', 'in', ['certified', 'in_progress'])
        ])
        expired_records.write({'status': 'expired'})

    def action_issue_certification(self):
        """Issue certification if verified"""
        self.ensure_one()
        if self.training_verified:
            self.status = 'certified'
            self.certification_date = fields.Date.context_today(self)
            self.message_post(body=f"NAID Certification {self.certification_number} issued for operator {self.name}.")
        else:
            raise ValueError("Cannot issue certification: Training not verified.")

    def _get_portal_url(self):
        """Get portal URL for customer access"""
        self.ensure_one()
        return f"/my/certification/{self.id}"

    # -------------------------------------------------------------
    # Placeholder button (XML reference) - Safe Stub
    # -------------------------------------------------------------
    def action_renew_certification(self):
        self.ensure_one()
        return False
