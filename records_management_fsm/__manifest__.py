{
    "name": "Records Management FSM Integration",
    "version": "18.0.1.0.0",
    "category": "Records Management",
    "summary": "FSM integration for Records Management",
    "author": "Your Name",
    "license": "LGPL-3",
    # Ensure all referenced actions exist (fleet vehicles menu uses fleet action)
    "depends": ["records_management", "project", "fleet"],
    # Optional dependency: uncomment if industry_fsm is available
    # "depends": ["records_management", "industry_fsm", "project", "fleet"],
    # Load order: security first, then data, then views/actions, menus last
    "data": [
        "security/ir.model.access.csv",
        "data/fsm_model_external_ids_data.xml",
        "views/enhanced_fsm_integration_views.xml",
        "views/fsm_notification_manager_views.xml",
        "views/fsm_notification_views.xml",
        "views/fsm_reschedule_wizard_views.xml",
        "views/fsm_task_service_line_views.xml",
        "views/fsm_task_views.xml",
        "views/mobile_fsm_integration_views.xml",
        # Menus loaded last to ensure actions above are available
        "views/fleet_fsm_integration_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "records_management_fsm/static/src/xml/fleet_fsm_dashboard.xml",
            "records_management_fsm/static/src/js/fleet_fsm_dashboard.js",
        ],
    },
    "installable": True,
    "auto_install": False,
}
