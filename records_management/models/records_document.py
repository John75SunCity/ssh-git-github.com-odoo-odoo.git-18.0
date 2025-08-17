from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RecordsDocument(models.Model):
    _name = 'records.document'
    _description = 'Records Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    partner_id = fields.Many2one()
    customer_inventory_id = fields.Many2one()
    document_type_id = fields.Many2one()
    description = fields.Text()
    reference = fields.Char()
    customer_id = fields.Many2one()
    container_id = fields.Many2one()
    location_id = fields.Many2one()
    retrieval_item_ids = fields.One2many()
    temp_inventory_id = fields.Many2one()
    lot_id = fields.Many2one()
    retention_policy_id = fields.Many2one()
    permanent_flag = fields.Boolean()
    permanent_flag_reason = fields.Selection()
    permanent_flag_date = fields.Datetime()
    permanent_flag_user_id = fields.Many2one()
    state = fields.Selection()
    received_date = fields.Date()
    creation_date = fields.Date()
    destruction_eligible_date = fields.Date()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    digitized = fields.Boolean(string='Digitized')
    digital_scan_ids = fields.One2many('records.digital.scan')
    chain_of_custody_ids = fields.One2many('records.chain.of.custody')
    audit_trail_ids = fields.One2many('naid.audit.log')
    compliance_verified = fields.Boolean(string='Compliance Verified')
    destruction_authorized_by = fields.Many2one('res.users')
    destruction_date = fields.Datetime(string='Destruction Date')
    destruction_method = fields.Char(string='Destruction Method')
    naid_destruction_verified = fields.Boolean(string='NAID Destruction Verified')
    action_audit_trail = fields.Char(string='Action Audit Trail')
    action_download = fields.Char(string='Action Download')
    action_mark_permanent = fields.Char(string='Action Mark Permanent')
    action_scan_document = fields.Char(string='Action Scan Document')
    action_schedule_destruction = fields.Char(string='Action Schedule Destruction')
    action_type = fields.Selection(string='Action Type')
    action_unmark_permanent = fields.Char(string='Action Unmark Permanent')
    action_view_chain_of_custody = fields.Char(string='Action View Chain Of Custody')
    audit = fields.Char(string='Audit')
    audit_trail_count = fields.Integer(string='Audit Trail Count')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    chain_of_custody_count = fields.Integer(string='Chain Of Custody Count')
    context = fields.Char(string='Context')
    created_date = fields.Date(string='Created Date')
    custody_chain = fields.Char(string='Custody Chain')
    days_until_destruction = fields.Char(string='Days Until Destruction')
    department_id = fields.Many2one('department')
    destroyed = fields.Char(string='Destroyed')
    destruction = fields.Char(string='Destruction')
    destruction_certificate_id = fields.Many2one('destruction.certificate')
    destruction_due = fields.Char(string='Destruction Due')
    destruction_facility = fields.Char(string='Destruction Facility')
    destruction_notes = fields.Char(string='Destruction Notes')
    destruction_this_month = fields.Char(string='Destruction This Month')
    destruction_witness = fields.Char(string='Destruction Witness')
    details = fields.Char(string='Details')
    digital = fields.Char(string='Digital')
    document_category = fields.Char(string='Document Category')
    event_date = fields.Date(string='Event Date')
    event_type = fields.Selection(string='Event Type')
    file_format = fields.Char(string='File Format')
    file_size = fields.Char(string='File Size')
    group_by_container = fields.Char(string='Group By Container')
    group_by_customer = fields.Char(string='Group By Customer')
    group_by_destruction = fields.Char(string='Group By Destruction')
    group_by_state = fields.Selection(string='Group By State')
    group_by_type = fields.Selection(string='Group By Type')
    help = fields.Char(string='Help')
    last_access_date = fields.Date(string='Last Access Date')
    location = fields.Char(string='Location')
    media_type = fields.Selection(string='Media Type')
    non_permanent = fields.Char(string='Non Permanent')
    notes = fields.Char(string='Notes')
    original_format = fields.Char(string='Original Format')
    pending_destruction = fields.Char(string='Pending Destruction')
    permanent = fields.Char(string='Permanent')
    permanent_flag_set_by = fields.Char(string='Permanent Flag Set By')
    permanent_flag_set_date = fields.Date(string='Permanent Flag Set Date')
    recent_access = fields.Char(string='Recent Access')
    res_model = fields.Char(string='Res Model')
    resolution = fields.Char(string='Resolution')
    responsible_person = fields.Char(string='Responsible Person')
    scan_date = fields.Date(string='Scan Date')
    search_view_id = fields.Many2one('search.view')
    signature_verified = fields.Boolean(string='Signature Verified')
    storage_date = fields.Date(string='Storage Date')
    storage_location = fields.Char(string='Storage Location')
    timestamp = fields.Char(string='Timestamp')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_audit_trail_count(self):
            for record in self:
                record.audit_trail_count = len(record.audit_trail_ids)


    def _compute_chain_of_custody_count(self):
            for record in self:
                record.chain_of_custody_count = len(record.chain_of_custody_ids)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_destruction_eligible_date(self):
            """Compute when document becomes eligible for destruction""":
            for record in self:
                if record.received_date and record.retention_policy_id and record.retention_policy_id.retention_years:
                    years = record.retention_policy_id.retention_years
                    record.destruction_eligible_date = record.received_date.replace(year=record.received_date.year + years)
                else:
                    record.destruction_eligible_date = False


    def _compute_state_from_flag(self):
            """Update state based on permanent flag status"""
            for record in self:
                if record.permanent_flag and record.state != 'destroyed':
                    record.state = 'flagged'

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_archive_document(self):
            """Archive the document"""

            self.ensure_one()
            if self.permanent_flag:
                raise UserError(_("Cannot archive document with permanent flag applied"))
            self.write({"state": "archived"})
            self.message_post(body=_("Document archived by %s", self.env.user.name))


    def action_activate_document(self):
            """Activate the document"""

            self.ensure_one()
            self.write({"state": "active"})
            self.message_post(body=_("Document activated by %s", self.env.user.name))


    def action_flag_permanent(self):
            """Apply permanent flag to document - opens wizard"""

            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Apply Permanent Flag'),
                'res_model': 'records.permanent.flag.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {}
                    'default_document_ids': [(6, 0, [self.id))],
                    'default_operation_type': 'apply',




    def action_remove_permanent_flag(self):
            """Remove permanent flag from document"""

            self.ensure_one()
            if not self.permanent_flag:
                raise UserError(_("Document does not have a permanent flag applied"))

            self.write({)}
                'permanent_flag': False,
                'permanent_flag_reason': False,
                'permanent_flag_date': False,
                'permanent_flag_user_id': False,
                'state': 'active',

            self.message_post(body=_("Permanent flag removed by %s", self.env.user.name))


    def action_view_audit_trail(self):
            """View document audit trail"""

            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Document Audit Trail'),
                'res_model': 'mail.message',
                'view_mode': 'tree,form',
                'domain': [('res_id', '=', self.id), ('model', '=', 'records.document')],
                'context': {'default_res_id': self.id, 'default_model': 'records.document'},


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_state_transitions(self):
            """Validate state transitions and permanent flag consistency"""
            for record in self:
                if record.state == "destroyed" and record.permanent_flag:
                    raise ValidationError(_("Cannot destroy document with permanent flag applied"))

                if record.permanent_flag and record.state not in ['flagged', 'active']:
                    raise ValidationError(_("Documents with permanent flags must be in 'Active' or 'Flagged' state"))


    def _check_permanent_flag_reason(self):
            """Ensure permanent flag has a reason when applied"""
            for record in self:
                if record.permanent_flag and not record.permanent_flag_reason:
                    raise ValidationError(_("Permanent flag reason is required when flag is applied"))

        # ============================================================================
            # LIFECYCLE METHODS
        # ============================================================================

    def create(self, vals_list):
            """Enhanced create method with audit trail"""
            documents = super().create(vals_list)
            for document in documents:
                document.message_post(body=_("Document created by %s", self.env.user.name))
            return documents


    def write(self, vals):
            """Enhanced write method with audit trail for critical changes""":
            result = super().write(vals)

            # Log critical field changes
            critical_fields = ['state', 'permanent_flag', 'permanent_flag_reason', 'retention_policy_id']
            changed_fields = [field for field in critical_fields if field in vals]:
            if changed_fields:
                for record in self:
                    changes = []
                    for field in changed_fields:
                        field_label = record._fields[field].string
                        if field in ['state', 'permanent_flag_reason']:
                            old_value = dict(record._fields[field].selection).get(vals[field]) if vals[field] else 'None':
                            changes.append(_("%s changed to %s", field_label, old_value))
                        elif field == 'permanent_flag':
                            changes.append(_("%s: %s", field_label, 'Applied' if vals[field] else 'Removed')):
                        else:
                            changes.append(_("%s updated", field_label))

                    if changes:
                        record.message_post(body=_("Document updated by %s: %s", self.env.user.name, ', '.join(changes)))

            return result

