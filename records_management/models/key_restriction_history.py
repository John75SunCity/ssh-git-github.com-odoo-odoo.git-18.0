from odoo import models, fields, api


class KeyRestrictionHistory(models.Model):
    _name = 'key.restriction.history'
    _description = 'Key Restriction History'
    _order = 'restriction_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string="History Entry Name",
        compute='_compute_name',
        store=True,
        help="Auto-generated name for this history entry"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        required=True,
        help="Partner this restriction history applies to"
    )

    restriction_date = fields.Datetime(
        string="Restriction Date",
        required=True,
        default=fields.Datetime.now,
        help="Date and time when the restriction was applied"
    )

    restriction_type = fields.Selection([
        ('impose', 'Restriction Imposed'),
        ('modify', 'Restriction Modified'),
        ('lift', 'Restriction Lifted'),
        ('temporary', 'Temporary Restriction'),
        ('permanent', 'Permanent Restriction')
    ], string="Restriction Type", required=True, help="Type of restriction action")

    restriction_status = fields.Selection([
        ('none', 'No Restrictions'),
        ('temporary', 'Temporary Restriction'),
        ('permanent', 'Permanent Restriction')
    ], string="Restriction Status", required=True, help="Status after this action")

    reason = fields.Text(
        string="Reason",
        required=True,
        help="Reason for the restriction action"
    )

    notes = fields.Text(
        string="Additional Notes",
        help="Additional notes about the restriction"
    )

    applied_by_id = fields.Many2one(
        'res.users',
        string="Applied By",
        required=True,
        default=lambda self: self.env.user,
        help="User who applied this restriction"
    )

    approved_by_id = fields.Many2one(
        'res.users',
        string="Approved By",
        help="User who approved this restriction action"
    )

    effective_until = fields.Datetime(
        string="Effective Until",
        help="Date until which the restriction is effective (for temporary restrictions)"
    )

    duration_days = fields.Integer(
        string="Duration (Days)",
        compute='_compute_duration',
        store=True,
        help="Duration of the restriction in days"
    )

    is_active = fields.Boolean(
        string="Currently Active",
        compute='_compute_is_active',
        store=True,
        help="Whether this restriction is currently active"
    )

    reference_document = fields.Char(
        string="Reference Document",
        help="Reference to any document supporting this restriction"
    )

    impact_level = fields.Selection([
        ('low', 'Low Impact'),
        ('medium', 'Medium Impact'),
        ('high', 'High Impact'),
        ('critical', 'Critical Impact')
    ], string="Impact Level", default='medium', help="Impact level of this restriction")

    communication_sent = fields.Boolean(
        string="Communication Sent",
        default=False,
        help="Whether notification has been sent to the partner"
    )

    communication_date = fields.Datetime(
        string="Communication Date",
        help="Date when notification was sent"
    )

    active = fields.Boolean(string="Active", default=True)

    @api.depends('restriction_type', 'partner_id.name', 'restriction_date')
    def _compute_name(self):
        """Compute the display name for the history entry"""
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else "Unknown"
            restriction_type = dict(record._fields['restriction_type'].selection).get(
                record.restriction_type, record.restriction_type
            )
            date_str = record.restriction_date.strftime('%Y-%m-%d %H:%M') if record.restriction_date else "No Date"
            record.name = f"{partner_name} - {restriction_type} - {date_str}"

    @api.depends('restriction_date', 'effective_until')
    def _compute_duration(self):
        """Compute the duration of the restriction in days"""
        for record in self:
            if record.restriction_date and record.effective_until:
                delta = record.effective_until - record.restriction_date
                record.duration_days = delta.days
            else:
                record.duration_days = 0

    @api.depends('restriction_type', 'restriction_status', 'effective_until')
    def _compute_is_active(self):
        """Determine if this restriction is currently active"""
        for record in self:
            now = fields.Datetime.now()
            if record.restriction_type == 'lift':
                record.is_active = False
            elif record.restriction_status == 'none':
                record.is_active = False
            elif record.restriction_status == 'permanent':
                record.is_active = True
            elif record.restriction_status == 'temporary':
                if record.effective_until:
                    record.is_active = now < record.effective_until
                else:
                    record.is_active = True
            else:
                record.is_active = False

    @api.model
    def create_restriction_entry(self, partner_id, restriction_type, restriction_status, reason, **kwargs):
        """Helper method to create a restriction history entry"""
        values = {
            'partner_id': partner_id,
            'restriction_type': restriction_type,
            'restriction_status': restriction_status,
            'reason': reason,
        }
        values.update(kwargs)
        return self.create(values)

    def action_send_notification(self):
        """Send notification about the restriction to the partner"""
        self.ensure_one()
        # Placeholder for notification logic
        self.write({
            'communication_sent': True,
            'communication_date': fields.Datetime.now()
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notification Sent',
                'message': f'Restriction notification sent for {self.partner_id.name}',
                'type': 'success'
            }
        }
