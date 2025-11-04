# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class TsheetsSyncLog(models.Model):
    _name = "qb.tsheets.sync.log"
    _description = "TSheets Sync Log"
    _order = "create_date desc"
    _rec_name = "sync_date"

    config_id = fields.Many2one(
        comodel_name="qb.tsheets.sync.config",
        string="Configuration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sync_date = fields.Datetime(
        string="Sync Date",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")
    status = fields.Selection([
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ], string="Status", required=True, default='success', index=True)
    
    total_fetched = fields.Integer(string="Total Fetched", default=0)
    total_created = fields.Integer(string="Created", default=0)
    total_updated = fields.Integer(string="Updated", default=0)
    total_failed = fields.Integer(string="Failed", default=0)
    
    message = fields.Text(string="Summary Message")
    error_details = fields.Text(string="Error Details")
    
    line_ids = fields.One2many(
        comodel_name="qb.tsheets.sync.log.line",
        inverse_name="log_id",
        string="Sync Details",
    )
    
    def action_export_csv(self):
        """Export sync log details to CSV"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/qb.tsheets.sync.log/{self.id}/export_csv',
            'target': 'new',
        }


class TsheetsSyncLogLine(models.Model):
    _name = "qb.tsheets.sync.log.line"
    _description = "TSheets Sync Log Line"
    _order = "id"

    log_id = fields.Many2one(
        comodel_name="qb.tsheets.sync.log",
        string="Sync Log",
        required=True,
        ondelete="cascade",
        index=True,
    )
    tsheets_id = fields.Char(string="TSheets ID", index=True)
    employee_name = fields.Char(string="Employee")
    date = fields.Date(string="Date")
    duration = fields.Float(string="Duration (hours)")
    project_name = fields.Char(string="Project")
    task_name = fields.Char(string="Task")
    
    status = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ], string="Status", required=True, index=True)
    
    timesheet_id = fields.Many2one(
        comodel_name="account.analytic.line",
        string="Timesheet Entry",
        ondelete="set null",
    )
    error_message = fields.Text(string="Error Message")
    raw_data = fields.Text(string="Raw TSheets Data")
