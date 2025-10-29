# -*- coding: utf-8 -*-

def post_init_hook(env):
    """
    Post-install hook to automatically grant TSheets access to Records Management users.
    This allows existing Records Management users to immediately use TSheets sync
    without manual group assignment.
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
