{
    "name": "QuickBooks TSheets Synchronization",
    "summary": "Sync TSheets time entries into Odoo timesheets with configurable mappings.",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "Records Management",
    "category": "Human Resources",
    "depends": [
        "base",
        "mail",
        "hr",
        "hr_timesheet",
        "project"
    ],
    "data": [
        "security/qb_tsheet_sync_groups.xml",
        "security/ir.model.access.csv",
        "views/tsheet_sync_config_views.xml",
        "views/tsheet_employee_map_views.xml",
        "wizards/tsheet_sync_wizard_views.xml",
        "data/ir_cron.xml"
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False
}
