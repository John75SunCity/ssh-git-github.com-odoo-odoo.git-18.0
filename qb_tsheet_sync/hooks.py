# -*- coding: utf-8 -*-

def post_init_hook(env):
    """
    Post-install hook to:
    1. Automatically grant TSheets access to Records Management users
    2. Clean up any action bindings that cause wizard auto-popup
    """
    _grant_tsheets_access(env)
    _cleanup_action_bindings(env)


def _grant_tsheets_access(env):
    """
    Grant TSheets access to Records Management and HR users.
    """
    # Get the TSheets User group
    tsheets_user_group = env.ref('qb_tsheet_sync.group_tsheets_user', raise_if_not_found=False)
    if not tsheets_user_group:
        return
    
    # Try to find Records Management user groups (if module is installed)
    rm_groups = env['res.groups'].search([
        ('name', 'ilike', 'records'),
        ('name', 'ilike', 'management')
    ])
    
    # Add all Records Management users to TSheets User group
    for rm_group in rm_groups:
        for user in rm_group.users:
            if tsheets_user_group not in user.groups_id:
                user.write({'groups_id': [(4, tsheets_user_group.id)]})
    
    # Also grant access to all HR users (since they likely need timesheet sync)
    hr_user_group = env.ref('hr.group_hr_user', raise_if_not_found=False)
    if hr_user_group:
        for user in hr_user_group.users:
            if tsheets_user_group not in user.groups_id:
                user.write({'groups_id': [(4, tsheets_user_group.id)]})


def _cleanup_action_bindings(env):
    """
    Remove any action bindings that cause the wizard to auto-popup.
    This prevents the sync wizard from appearing when users click on Timesheets.
    """
    # Remove bindings from our wizard action
    wizard_action = env.ref('qb_tsheet_sync.action_tsheets_sync_wizard', raise_if_not_found=False)
    if wizard_action:
        # Clear any model bindings
        wizard_action.write({
            'binding_model_id': False,
            'binding_view_types': False,
        })
    
    # Find and clean up the auto-created server action from cron
    cron_action = env.ref('qb_tsheet_sync.ir_cron_tsheets_sync', raise_if_not_found=False)
    if cron_action and hasattr(cron_action, 'ir_actions_server_id'):
        server_action = cron_action.ir_actions_server_id
        if server_action:
            # Remove any bindings from the server action
            server_action.write({
                'binding_model_id': False,
                'binding_view_types': False,
            })
    
    # Search for any orphaned server actions related to TSheets
    orphaned_actions = env['ir.actions.server'].search([
        ('name', 'ilike', 'tsheet'),
        ('binding_model_id', '!=', False)
    ])
    for action in orphaned_actions:
        action.write({
            'binding_model_id': False,
            'binding_view_types': False,
        })
