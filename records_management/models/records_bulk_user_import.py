import base64
import csv
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsBulkUserImport(models.Model):
    _name = 'records.bulk.user.import'
    _description = 'Records Bulk User Import'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Import Batch Name', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    csv_file = fields.Binary(string='CSV File', required=True, help="Upload a CSV file with columns: name, login, email")
    filename = fields.Char(string='Filename')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], string='Status', default='draft', readonly=True)
    log = fields.Text(string="Import Log", readonly=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.bulk.user.import') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_import_users(self):
        """
        Parses the uploaded CSV file and creates new users.
        Expected CSV header: name,login,email
        """
        self.ensure_one()
        if not self.csv_file:
            raise UserError(_("Please upload a CSV file to import."))

        log_lines = []
        try:
            # Decode the binary file content
            decoded_file = base64.b64decode(self.csv_file).decode('utf-8')
            csv_reader = csv.DictReader(StringIO(decoded_file))

            if not all(key in csv_reader.fieldnames for key in ['name', 'login', 'email']):
                raise UserError(_("CSV file must have the following headers: name, login, email"))

            for row in csv_reader:
                user_name = row.get('name')
                user_login = row.get('login')
                user_email = row.get('email')

                if not all([user_name, user_login, user_email]):
                    log_lines.append(f"Skipping row due to missing data: {row}")
                    continue

                # Check if user already exists
                if self.env['res.users'].search(['|', ('login', '=', user_login), ('email', '=', user_email)]):
                    log_lines.append(f"User '{user_name}' with login '{user_login}' or email '{user_email}' already exists. Skipping.")
                    continue

                # Create the new user
                self.env['res.users'].create({
                    'name': user_name,
                    'login': user_login,
                    'email': user_email,
                    # Add user to a default group if necessary
                    'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
                })
                log_lines.append(f"Successfully created user: {user_name} ({user_login})")

            self.write({
                'state': 'done',
                'log': "\n".join(log_lines)
            })
            self.message_post(body=_("User import completed successfully."))

        except Exception as e:
            self.write({
                'state': 'error',
                'log': f"An error occurred during import:\n{e}\n\n" + "\n".join(log_lines)
            })
            raise UserError(_("An error occurred during the import process. Please check the log for details. Error: %s") % e) from e

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

