# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


class HardDriveScanWizard(models.TransientModel):
    """
    A streamlined wizard for barcode scanning of hard drives during pickup and verification.
    Supports both one-step (manager bypass) and two-step verification workflows.
    Focuses on user-friendly scanning rather than complex inventory management.
    """
    _name = 'hard.drive.scan.wizard'
    _description = 'Hard Drive Scanning Wizard'

    # ============================================================================
    # WIZARD FIELDS
    # ============================================================================
    fsm_task_id = fields.Many2one(
        'project.task',
        string="Work Order",
        required=True,
        domain="[('is_fsm', '=', True)]",
        help="The Field Service work order for hard drive destruction."
    )
    partner_id = fields.Many2one(related='fsm_task_id.partner_id', string="Customer", readonly=True)

    # Workflow control
    scan_step = fields.Selection([
        ('pickup', 'Pickup at Customer'),
        ('verification', 'Verification at Facility'),
        ('single_step', 'Single Step (Manager Override)')
    ], string="Scan Step", default='pickup', required=True)

    two_step_verification = fields.Boolean(
        string="Two-Step Verification",
        default=True,
        help="Enable two-step verification (pickup + facility verification)"
    )

    # Manager override
    manager_bypass = fields.Boolean(
        string="Manager Bypass",
        default=False,
        help="Managers can bypass two-step verification for faster processing"
    )

    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('degaussing', 'Degaussing'),
        ('disintegration', 'Disintegration')
    ], string="Destruction Method", required=True, default='shredding')

    scan_line_ids = fields.One2many(
        'hard.drive.scan.wizard.line',
        'wizard_id',
        string="Scanned Hard Drives"
    )

    # Text area for bulk serial number entry
    serial_numbers_text = fields.Text(
        string="Scan or Enter Serial Numbers",
        help="Scan barcodes or enter serial numbers, one per line. Click 'Add to List' to process."
    )

    # Summary fields
    total_drives_count = fields.Integer(string="Total Drives", compute="_compute_drive_counts")
    verified_drives_count = fields.Integer(string="Verified Drives", compute="_compute_drive_counts")

    @api.depends('scan_line_ids')
    def _compute_drive_counts(self):
        for wizard in self:
            wizard.total_drives_count = len(wizard.scan_line_ids)
            wizard.verified_drives_count = len(wizard.scan_line_ids.filtered('verified'))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_process_scanned_serials(self):
        """Processes the serial numbers entered in the text area."""
        self.ensure_one()
        if not self.serial_numbers_text:
            return

        serials = [s.strip() for s in self.serial_numbers_text.splitlines() if s.strip()]
        if not serials:
            return

        existing_serials = [line.serial_number for line in self.scan_line_ids]

        lines_to_create = []
        for serial in serials:
            if serial not in existing_serials:
                lines_to_create.append({'wizard_id': self.id, 'serial_number': serial})

        if lines_to_create:
            self.env['hard.drive.scan.wizard.line'].create(lines_to_create)

        # Clear the text area after processing
        self.serial_numbers_text = False

        # Return a new action to reopen the wizard form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_destruction(self):
        """
        Confirms the destruction of all scanned hard drives, creates the
        shredding.hard_drive records, links them to the FSM task, and
        generates a Certificate of Destruction.
        """
        self.ensure_one()
        if not self.scan_line_ids:
            raise UserError(_("You must scan at least one hard drive serial number."))

        hard_drive_vals_list = []
        for line in self.scan_line_ids:
            hard_drive_vals_list.append({
                'serial_number': line.serial_number,
                'fsm_task_id': self.fsm_task_id.id,
                'partner_id': self.partner_id.id,
                'destruction_method': self.destruction_method,
                'state': 'destroyed', # Mark as destroyed immediately
                'destruction_date': fields.Datetime.now(),
                'destruction_technician_id': self.env.user.id,
            })

        if not hard_drive_vals_list:
            raise UserError(_("No valid hard drives to process."))

        # Create the hard drive records
        hard_drives = self.env['shredding.hard_drive'].create(hard_drive_vals_list)

        # Generate Certificate of Destruction
        certificate = self.env['shredding.certificate'].create({
            'partner_id': self.partner_id.id,
            'fsm_task_id': self.fsm_task_id.id,
            'destruction_date': fields.Datetime.now(),
            'hard_drive_ids': [(6, 0, hard_drives.ids)],
        })

        # Link certificate back to hard drives
        hard_drives.write({'certificate_id': certificate.id, 'state': 'certified'})

        # Post a message on the FSM task chatter
        cert_url = certificate.get_portal_url()
        body = _(
            'Successfully destroyed and certified %(drive_count)s hard drives. Certificate: <a href="%(url)s">%(name)s</a>',
            drive_count=len(hard_drives),
            url=cert_url,
            name=certificate.name
        )
        self.fsm_task_id.message_post(
            body=body,
            subject=_("Hard Drive Destruction Complete")
        )

        # Mark the FSM task as done
        self.fsm_task_id.action_fsm_validate()

        # Return an action to view the generated certificate
        return {
            'name': _('Certificate of Destruction'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'shredding.certificate',
            'res_id': certificate.id,
            'target': 'current',
        }

    def action_add_serial_line(self):
        """Add a single serial number line for manual entry."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hard.drive.scan.wizard.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_wizard_id': self.id},
        }

    def action_verify_selected(self):
        """Mark selected drives as verified (for two-step verification)."""
        self.ensure_one()
        # Mark all unverified drives as verified
        unverified_lines = self.scan_line_ids.filtered(lambda l: not l.verified)
        unverified_lines.write({
            'verified': True,
            'scanned_at_facility': fields.Datetime.now()
        })
        return {'type': 'ir.actions.do_nothing'}

    def action_manager_bypass(self):
        """Manager bypass for single-step verification."""
        self.ensure_one()
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can bypass two-step verification."))

        self.write({
            'manager_bypass': True,
            'scan_step': 'single_step',
            'two_step_verification': False
        })
        # Mark all drives as verified
        self.scan_line_ids.write({'verified': True})
        return {'type': 'ir.actions.do_nothing'}


class HardDriveScanWizardLine(models.TransientModel):
    """Lines for the Hard Drive Scanning Wizard."""
    _name = 'hard.drive.scan.wizard.line'
    _description = 'Hard Drive Scanning Wizard Line'

    wizard_id = fields.Many2one(comodel_name='hard.drive.scan.wizard', string="Wizard", required=True, ondelete='cascade')
    serial_number = fields.Char(string="Serial Number", required=True)
    verified = fields.Boolean(
        string="Verified",
        default=False,
        help="Check when this drive is verified at facility (two-step verification)"
    )
    scanned_at_pickup = fields.Datetime(string="Pickup Scan Time", readonly=True)
    scanned_at_facility = fields.Datetime(string="Facility Scan Time", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-timestamp based on wizard context
            wizard = self.env['hard.drive.scan.wizard'].browse(vals.get('wizard_id'))
            if wizard.scan_step == 'pickup':
                vals['scanned_at_pickup'] = fields.Datetime.now()
            elif wizard.scan_step == 'verification':
                vals['scanned_at_facility'] = fields.Datetime.now()
                vals['verified'] = True
        return super().create(vals_list)

    _sql_constraints = [
        ('_serial_number_wizard_uniq', 'unique(wizard_id, serial_number)', _('Serial numbers must be unique within a single scan session.')),
    ]
