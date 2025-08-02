# -*- coding: utf-8 -*-
"""
Views and Security for Live Monitoring System
"""

# Security groups and access rules
security_xml = """
<odoo>
    <data noupdate="1">
        <!-- Monitoring Security Group -->
        <record id="group_monitoring_user" model="res.groups">
            <field name="name">Monitoring User</field>
            <field name="category_id" ref="base.module_category_hidden"/>
            <field name="comment">Can view monitoring data</field>
        </record>

        <record id="group_monitoring_manager" model="res.groups">
            <field name="name">Monitoring Manager</field>
            <field name="category_id" ref="base.module_category_hidden"/>
            <field name="comment">Can manage monitoring system</field>
            <field name="implied_ids" eval="[(4, ref('group_monitoring_user'))]"/>
        </record>

        <!-- Add monitoring access to system administrators -->
        <record id="base.group_system" model="res.groups">
            <field name="implied_ids" eval="[(4, ref('group_monitoring_manager'))]"/>
        </record>
    </data>
</odoo>
"""

# Access control for monitoring model
access_csv = """
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_records_management_monitor_user,records.management.monitor.user,model_records_management_monitor,group_monitoring_user,1,0,0,0
access_records_management_monitor_manager,records.management.monitor.manager,model_records_management_monitor,group_monitoring_manager,1,1,1,1
"""

# View definitions
views_xml = """
<odoo>
    <data>
        <!-- Tree View -->
        <record id="view_records_management_monitor_tree" model="ir.ui.view">
            <field name="name">records.management.monitor.tree</field>
            <field name="model">records.management.monitor</field>
            <field name="arch" type="xml">
                <tree string="Monitoring Logs" 
                    decoration-danger="severity in ['critical', 'emergency']"
                    decoration-warning="severity == 'high'"
                    decoration-info="severity == 'medium'"
                    default_order="create_date desc">
                    <field name="create_date"/>
                    <field name="monitor_type"/>
                    <field name="severity"/>
                    <field name="name"/>
                    <field name="affected_model"/>
                    <field name="user_id"/>
                    <field name="status"/>
                    <field name="occurrence_count"/>
                </tree>
            </field>
        </record>

        <!-- Form View -->
        <record id="view_records_management_monitor_form" model="ir.ui.view">
            <field name="name">records.management.monitor.form</field>
            <field name="model">records.management.monitor</field>
            <field name="arch" type="xml">
                <form string="Monitoring Entry">
                    <header>
                        <button name="action_resolve" string="Mark Resolved" 
                                type="object" class="btn-success"
                                states="new,investigating"/>
                        <button name="action_investigate" string="Investigate" 
                                type="object" class="btn-warning"
                                states="new"/>
                        <button name="action_ignore" string="Ignore" 
                                type="object" class="btn-secondary"
                                states="new,investigating"/>
                        <field name="status" widget="statusbar"/>
                    </header>
                    <sheet>
                        <div class="oe_title">
                            <h1><field name="name"/></h1>
                        </div>
                        <group>
                            <group>
                                <field name="monitor_type"/>
                                <field name="severity"/>
                                <field name="create_date"/>
                                <field name="user_id"/>
                                <field name="company_id"/>
                            </group>
                            <group>
                                <field name="affected_model"/>
                                <field name="affected_method"/>
                                <field name="affected_record_id"/>
                                <field name="occurrence_count"/>
                                <field name="first_occurrence"/>
                                <field name="last_occurrence"/>
                            </group>
                        </group>

                        <notebook>
                            <page string="Error Details" attrs="{'invisible': [('monitor_type', '!=', 'error')]}">
                                <group>
                                    <field name="error_message" widget="text"/>
                                    <field name="error_traceback" widget="text"/>
                                    <field name="error_context" widget="text"/>
                                </group>
                            </page>

                            <page string="Performance" attrs="{'invisible': [('monitor_type', '!=', 'performance')]}">
                                <group>
                                    <field name="execution_time"/>
                                    <field name="memory_usage"/>
                                    <field name="cpu_usage"/>
                                </group>
                            </page>

                            <page string="Session Info">
                                <group>
                                    <field name="session_id"/>
                                    <field name="ip_address"/>
                                    <field name="user_agent"/>
                                </group>
                            </page>

                            <page string="Resolution" attrs="{'invisible': [('status', 'in', ['new'])]}">
                                <group>
                                    <field name="resolved_by"/>
                                    <field name="resolved_date"/>
                                    <field name="resolution_notes" widget="text"/>
                                </group>
                            </page>

                            <page string="Notifications">
                                <group>
                                    <field name="notification_sent"/>
                                    <field name="webhook_sent"/>
                                    <field name="email_sent"/>
                                </group>
                            </page>
                        </notebook>
                    </sheet>
                    <div class="oe_chatter">
                        <field name="message_follower_ids" widget="mail_followers"/>
                        <field name="activity_ids" widget="mail_activity"/>
                        <field name="message_ids" widget="mail_thread"/>
                    </div>
                </form>
            </field>
        </record>

        <!-- Search View -->
        <record id="view_records_management_monitor_search" model="ir.ui.view">
            <field name="name">records.management.monitor.search</field>
            <field name="model">records.management.monitor</field>
            <field name="arch" type="xml">
                <search>
                    <field name="name"/>
                    <field name="error_message"/>
                    <field name="affected_model"/>
                    <field name="user_id"/>

                    <filter name="errors" string="Errors" domain="[('monitor_type', '=', 'error')]"/>
                    <filter name="warnings" string="Warnings" domain="[('monitor_type', '=', 'warning')]"/>
                    <filter name="performance" string="Performance" domain="[('monitor_type', '=', 'performance')]"/>
                    <filter name="health_checks" string="Health Checks" domain="[('monitor_type', '=', 'health_check')]"/>

                    <separator/>
                    <filter name="critical" string="Critical" domain="[('severity', 'in', ['critical', 'emergency'])]"/>
                    <filter name="high" string="High Priority" domain="[('severity', '=', 'high')]"/>
                    <filter name="unresolved" string="Unresolved" domain="[('status', 'in', ['new', 'investigating'])]"/>

                    <separator/>
                    <filter name="today" string="Today" domain="[('create_date', '>=', context_today().strftime('%Y-%m-%d'))]"/>
                    <filter name="this_week" string="This Week" domain="[('create_date', '>=', (context_today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'))]"/>

                    <group expand="0" string="Group By">
                        <filter name="group_by_type" string="Type" domain="[]" context="{'group_by': 'monitor_type'}"/>
                        <filter name="group_by_severity" string="Severity" domain="[]" context="{'group_by': 'severity'}"/>
                        <filter name="group_by_model" string="Model" domain="[]" context="{'group_by': 'affected_model'}"/>
                        <filter name="group_by_user" string="User" domain="[]" context="{'group_by': 'user_id'}"/>
                        <filter name="group_by_status" string="Status" domain="[]" context="{'group_by': 'status'}"/>
                        <filter name="group_by_date" string="Date" domain="[]" context="{'group_by': 'create_date:day'}"/>
                    </group>
                </search>
            </field>
        </record>

        <!-- Actions -->
        <record id="action_records_management_monitor" model="ir.actions.act_window">
            <field name="name">Live Monitoring</field>
            <field name="res_model">records.management.monitor</field>
            <field name="view_mode">tree,form</field>
            <field name="context">{'search_default_unresolved': 1, 'search_default_today': 1}</field>
            <field name="help" type="html">
                <p class="o_view_nocontent_smiling_face">
                    Live Monitoring System
                </p>
                <p>
                    This system monitors Records Management module in real-time.<br/>
                    Errors, performance issues, and system health are tracked automatically.
                </p>
            </field>
        </record>

        <!-- Dashboard Action -->
        <record id="action_monitoring_dashboard" model="ir.actions.act_window">
            <field name="name">Monitoring Dashboard</field>
            <field name="res_model">records.management.monitor</field>
            <field name="view_mode">graph,pivot,tree</field>
            <field name="domain">[]</field>
            <field name="context">{
                'search_default_this_week': 1,
                'group_by': ['create_date:day', 'monitor_type']
            }</field>
        </record>

        <!-- Menu Items -->
        <menuitem id="menu_monitoring_root" 
                name="Monitoring" 
                parent="records_management.menu_root"
                sequence="100"
                groups="group_monitoring_user"/>

        <menuitem id="menu_monitoring_logs" 
                name="Monitoring Logs" 
                parent="menu_monitoring_root"
                action="action_records_management_monitor"
                sequence="10"/>

        <menuitem id="menu_monitoring_dashboard" 
                name="Dashboard" 
                parent="menu_monitoring_root"
                action="action_monitoring_dashboard"
                sequence="20"/>
    </data>
</odoo>
"""

# Scheduled actions for monitoring
scheduled_actions_xml = """
<odoo>
    <data noupdate="1">
        <!-- Health Check Cron -->
        <record id="cron_health_check" model="ir.cron">
            <field name="name">Records Management: Health Check</field>
            <field name="model_id" ref="model_records_management_monitor"/>
            <field name="state">code</field>
            <field name="code">model.health_check()</field>
            <field name="interval_number">15</field>
            <field name="interval_type">minutes</field>
            <field name="numbercall">-1</field>
            <field name="doall" eval="False"/>
            <field name="active" eval="True"/>
        </record>

        <!-- Cleanup Old Logs Cron -->
        <record id="cron_cleanup_logs" model="ir.cron">
            <field name="name">Records Management: Cleanup Old Monitoring Logs</field>
            <field name="model_id" ref="model_records_management_monitor"/>
            <field name="state">code</field>
            <field name="code">model.cleanup_old_logs(days=30)</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="numbercall">-1</field>
            <field name="doall" eval="False"/>
            <field name="active" eval="True"/>
        </record>
    </data>
</odoo>
"""

print("Monitoring system views and security configuration ready!")
print("\nTo implement:")
print("1. Add security XML to security/monitoring_security.xml")
print("2. Add access CSV to security/monitoring_access.csv") 
print("3. Add views XML to views/monitoring_views.xml")
print("4. Add scheduled actions to data/monitoring_crons.xml")
