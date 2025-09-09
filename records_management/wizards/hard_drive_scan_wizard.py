# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class HardDriveScanWizard(models.TransientModel):
    """
    A wizard to facilitate the bulk scanning of hard drive serial numbers,
    associating them with a specific Field Service task, and automating
    the creation of a Certificate of Destruction upon completion.
    """
    _name = 'hard.drive.scan.wizard'
    _description = 'Hard Drive Scanning Wizard'

    fsm_task_id = fields.Many2one(
        'project.task',
        string="FSM Task",
        required=True,
        domain="[('is_fsm', '=', True), ('allow_hard_drive_destruction', '=', True)]",
        help="The Field Service task for hard drive destruction."
    )
    partner_id = fields.Many2one(related='fsm_task_id.partner_id', string="Customer", readonly=True)
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

    serial_numbers_text = fields.Text(
        string="Enter Serial Numbers",
        help="Enter one serial number per line. Click 'Process Scanned Serials' to add them to the list below."
    )

    def action_process_scanned_serials(self):
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
        self.serial_numbers_text = False
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_destruction(self):
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
                'state': 'destroyed',
                'destruction_date': fields.Datetime.now(),
                'destruction_technician_id': self.env.user.id,
            })
        if not hard_drive_vals_list:
            raise UserError(_("No valid hard drives to process."))
        hard_drives = self.env['shredding.hard_drive'].create(hard_drive_vals_list)
        certificate = self.env['shredding.certificate'].create({
            'partner_id': self.partner_id.id,
            'fsm_task_id': self.fsm_task_id.id,
            'destruction_date': fields.Datetime.now(),
            'hard_drive_ids': [(6, 0, hard_drives.ids)],
        })
        hard_drives.write({'certificate_id': certificate.id, 'state': 'certified'})
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
        self.fsm_task_id.action_fsm_validate()
        return {
            'name': _('Certificate of Destruction'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'shredding.certificate',
            'res_id': certificate.id,
            'target': 'current',
        }


class HardDriveScanWizardLine(models.TransientModel):
    _name = 'hard.drive.scan.wizard.line'
    _description = 'Hard Drive Scanning Wizard Line'
    wizard_id = fields.Many2one('hard.drive.scan.wizard', string="Wizard", required=True, ondelete='cascade')
    serial_number = fields.Char(string="Serial Number", required=True)
    _sql_constraints = [
        ('serial_number_wizard_uniq', 'unique(wizard_id, serial_number)', 'Serial numbers must be unique within a single scan session.')
    ]
