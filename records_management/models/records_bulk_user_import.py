import base64
import csv
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError


class RecordsBulkUserImport(models.Model):
    _name = 'records.bulk.user.import'
    _description = 'Records Bulk User Import'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Import Batch Name', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    csv_file = fields.Binary(
        string="CSV File",
        required=True,
        # Updated: Clarify expected columns and behavior for consistency with code logic
        help="Upload a CSV file with columns: name, email. The 'login' field will be automatically set to the email value.",
    )
    filename = fields.Char(string='Filename')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], string='Status', default='draft', readonly=True)
    log = fields.Text(string="Import Log", readonly=True)
    # New field for configurable group assignment
    default_group_ids = fields.Many2many(
        "res.groups",
        "records_bulk_user_import_groups_rel",
        "bulk_import_id",
        "group_id",
        string="Default User Groups",
        help="Groups to assign to newly created users. If empty, defaults to 'base.group_user'.",
    )

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
    # CONSTRAINTS
    # ============================================================================
    @api.constrains("csv_file")
    def _check_csv_file(self):
        """Validate CSV file format before processing."""
        if self.csv_file:
            try:
                content = base64.b64decode(self.csv_file).decode("utf-8")
                csv_reader = csv.reader(StringIO(content))
                headers = next(csv_reader, None)
                # Updated: Make error message more descriptive and consistent with help text
                if not headers or len(headers) < 2:  # Assume at least name and email
                    raise ValidationError(
                        _(
                            "Invalid CSV format. Expected at least 2 columns with headers like 'name,email'. The 'login' field will be set to the email value."
                        )
                    )
            except Exception as exc:
                raise ValidationError(_("Unable to parse CSV file. Ensure it's UTF-8 encoded and properly formatted as CSV.")) from exc

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_import_users(self):
        """Import users from CSV with enhanced error handling and security."""
        self.ensure_one()  # Added: Odoo standard for action methods
        if not self.env.user.has_group("records_management.group_records_manager"):
            raise AccessError(_("Only managers can perform bulk user imports."))

        if not self.csv_file:
            raise UserError(_("Please upload a CSV file."))

        log_lines = []
        content = base64.b64decode(self.csv_file).decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        headers = next(csv_reader, None)

        if not headers:
            raise UserError(_("CSV file is empty or invalid."))

        # Assume CSV has columns: name, email, [optional: groups]
        # Updated: Add comment for clarity on column handling
        name_idx = headers.index("name") if "name" in headers else 0
        email_idx = headers.index("email") if "email" in headers else 1

        users_to_create = []
        for row_num, row in enumerate(csv_reader, start=2):
            if len(row) <= max(name_idx, email_idx):
                log_lines.append(_("Row %s: Insufficient columns.", row_num))
                continue

            user_name = row[name_idx].strip()
            user_email = row[email_idx].strip()

            if not user_name or not user_email:
                log_lines.append(_("Row %s: Missing name or email.", row_num))
                continue

            # Prepare user data
            # Note: 'login' is set to 'user_email' as per code logic (no separate 'login' column expected)
            user_vals = {
                "name": user_name,
                "login": user_email,
                "email": user_email,
                "groups_id": [
                    (
                        6,
                        0,
                        self.default_group_ids.ids if self.default_group_ids else [self.env.ref("base.group_user").id],
                    )
                ],
            }
            users_to_create.append(user_vals)

        # Batch create users
        if users_to_create:
            try:
                self.env["res.users"].create(users_to_create)
                log_lines.append(_("Successfully imported %s users.", len(users_to_create)))
                # Log to audit trail for compliance
                self.env["naid.audit.log"].create(
                    {
                        "action": "bulk_user_import",
                        "details": _("Imported %s users via CSV.", len(users_to_create)),
                        "user_id": self.env.user.id,
                    }
                )
            except Exception as e:
                log_lines.append(_("Error creating users: %s", str(e)))

        self.write(
            {
                "state": "done" if not any("Error" in line for line in log_lines) else "error",
                "log": "\n".join(log_lines),
            }
        )
        self.message_post(body=_("User import completed. Check log for details."))
