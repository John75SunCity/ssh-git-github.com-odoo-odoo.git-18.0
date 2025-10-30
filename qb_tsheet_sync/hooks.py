# -*- coding: utf-8 -*-

def post_init_hook(env):
    """
    Post-install hook to automatically grant TSheets access to Records Management users
    and clean up any incorrect action bindings.
    """
    # CRITICAL: Remove any action bindings that cause the wizard to auto-popup
    _cleanup_action_bindings(env)
    
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
    Remove any action bindings that cause the TSheets sync wizard or cron
    to auto-popup when accessing timesheets.
    
    This fixes the issue where the wizard appears every time you click Timesheets.
    """
    # Find our wizard action
    wizard_action = env.ref('qb_tsheet_sync.action_tsheets_sync_wizard', raise_if_not_found=False)
    if wizard_action:
        # Remove any view bindings (these cause auto-popup)
        wizard_action.write({
            'binding_model_id': False,
            'binding_view_types': False,
        })
    
    # Find the cron's underlying server action (Odoo creates one internally)
    cron = env.ref('qb_tsheet_sync.ir_cron_tsheets_sync', raise_if_not_found=False)
    if cron and cron.ir_actions_server_id:
        # Remove any view bindings from the cron's server action
        cron.ir_actions_server_id.write({
            'binding_model_id': False,
            'binding_view_types': False,
        })
    
    # Also search for any orphaned server actions with similar names
    orphaned_actions = env['ir.actions.server'].search([
        '|', '|',
        ('name', '=', 'TSheets Synchronization'),
        ('name', 'ilike', 'tsheets%sync%'),
        ('name', 'ilike', 'sync%tsheets%'),
    ])
    for action in orphaned_actions:
        # Remove bindings from any TSheets-related server actions
        if action.binding_model_id:
            action.write({
                'binding_model_id': False,
                'binding_view_types': False,
            })
