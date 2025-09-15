from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class BinIssueReportWizard(models.TransientModel):
    """
    Wizard for reporting bin issues such as damage, missing bins, or service problems.
    
    This wizard allows users to report various types of bin issues and automatically
    creates service tickets or work orders as needed.
    """
    
    _name = 'bin.issue.report.wizard'
    _description = 'Bin Issue Report Wizard'

    # Basic Information
    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string='Bin',
        required=True,
        help='The bin that has an issue'
    )
    
    issue_type = fields.Selection([
        ('damage', 'Physical Damage'),
        ('missing', 'Missing Bin'),
        ('full', 'Bin Full - Needs Service'),
        ('placement', 'Incorrect Placement'),
        ('access', 'Access Issues'),
        ('contamination', 'Contamination'),
        ('other', 'Other Issue')
    ], string='Issue Type', required=True, default='damage')
    
    description = fields.Text(
        string='Issue Description',
        required=True,
        help='Detailed description of the issue'
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium', required=True)
    
    # Reporter Information
    reported_by = fields.Many2one(
        comodel_name='res.users',
        string='Reported By',
        default=lambda self: self.env.user,
        required=True
    )
    
    report_date = fields.Datetime(
        string='Report Date',
        default=fields.Datetime.now,
        required=True
    )
    
    # Customer Information
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='bin_id.current_customer_id',
        readonly=True
    )
    
    # Photos/Evidence
    photo_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='bin_issue_photo_rel',
        column1='wizard_id',
        column2='attachment_id',
        string='Photos',
        help='Upload photos of the issue'
    )
    
    # Actions
    requires_immediate_action = fields.Boolean(
        string='Requires Immediate Action',
        help='Check if this issue requires immediate attention'
    )
    
    create_work_order = fields.Boolean(
        string='Create Work Order',
        default=True,
        help='Automatically create a work order for this issue'
    )
    
    notify_customer = fields.Boolean(
        string='Notify Customer',
        default=True,
        help='Send notification to customer about the issue'
    )
    
    # Computed Fields
    bin_barcode = fields.Char(
        string='Bin Barcode',
        related='bin_id.barcode',
        readonly=True
    )
    
    current_location = fields.Char(
        string='Current Location',
        related='bin_id.current_location',
        readonly=True
    )

    @api.onchange('issue_type')
    def _onchange_issue_type(self):
        """Set default priority and actions based on issue type"""
        if self.issue_type == 'missing':
            self.priority = 'high'
            self.requires_immediate_action = True
        elif self.issue_type == 'damage':
            self.priority = 'medium'
            self.requires_immediate_action = True
        elif self.issue_type == 'contamination':
            self.priority = 'high'
            self.requires_immediate_action = True
        elif self.issue_type == 'full':
            self.priority = 'medium'
            self.create_work_order = True
    
    def action_submit_report(self):
        """Submit the bin issue report and create necessary records"""
        self.ensure_one()
        
        # Validate required fields
        if not self.description or len(self.description.strip()) < 10:
            raise ValidationError(_("Please provide a detailed description (at least 10 characters)."))
        
        # Create issue record
        issue_vals = {
            'bin_id': self.bin_id.id,
            'issue_type': self.issue_type,
            'description': self.description,
            'priority': self.priority,
            'reported_by': self.reported_by.id,
            'report_date': self.report_date,
            'requires_immediate_action': self.requires_immediate_action,
            'state': 'reported'
        }
        
        # Create bin issue record (if model exists)
        if hasattr(self.env, 'bin.issue'):
            issue = self.env['bin.issue'].create(issue_vals)
        else:
            # Create as activity or mail message if no dedicated model
            self.bin_id.activity_schedule(
                'records_management.mail_activity_bin_issue',
                note=f"Issue Report: {self.issue_type}\n\n{self.description}",
                user_id=self.env.user.id
            )
        
        # Create work order if requested
        if self.create_work_order:
            self._create_work_order()
        
        # Send notifications
        if self.notify_customer and self.customer_id:
            self._send_customer_notification()
        
        # Update bin status if needed
        if self.issue_type in ['damage', 'contamination']:
            self.bin_id.write({'status': 'maintenance'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Issue Reported'),
                'message': _('Bin issue has been reported successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _create_work_order(self):
        """Create a work order for the bin issue"""
        work_order_vals = {
            'name': f"Bin Issue: {self.issue_type} - {self.bin_barcode}",
            'project_id': self.env.ref('industry_fsm.fsm_project').id,
            'partner_id': self.customer_id.id if self.customer_id else False,
            'description': f"Issue Type: {self.issue_type}\n\nDescription:\n{self.description}",
            'priority': '1' if self.priority == 'urgent' else '0',
            'tag_ids': [(6, 0, [self.env.ref('records_management.tag_bin_issue').id])] if self.env.ref('records_management.tag_bin_issue', False) else False
        }
        
        work_order = self.env['project.task'].create(work_order_vals)
        
        # Link photos to work order
        if self.photo_ids:
            for photo in self.photo_ids:
                photo.write({'res_model': 'project.task', 'res_id': work_order.id})
        
        return work_order
    
    def _send_customer_notification(self):
        """Send notification to customer about the bin issue"""
        if not self.customer_id.email:
            return
        
        template = self.env.ref('records_management.email_template_bin_issue', False)
        if template:
            template.send_mail(self.id, force_send=True)
        else:
            # Fallback: send simple notification
            mail_values = {
                'subject': f'Bin Issue Report - {self.bin_barcode}',
                'body_html': f"""
                    <p>Dear {self.customer_id.name},</p>
                    <p>We have received a report regarding bin {self.bin_barcode} at your location:</p>
                    <ul>
                        <li><strong>Issue Type:</strong> {self.issue_type}</li>
                        <li><strong>Priority:</strong> {self.priority}</li>
                        <li><strong>Description:</strong> {self.description}</li>
                    </ul>
                    <p>We will address this issue promptly and keep you updated on our progress.</p>
                    <p>Thank you for your cooperation.</p>
                """,
                'email_to': self.customer_id.email,
                'email_from': self.env.user.email,
            }
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
