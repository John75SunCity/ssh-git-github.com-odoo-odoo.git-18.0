# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FsmNotificationManager(models.Model):
    """FSM Notification Manager for field service management integration"""

    _name = "fsm.notification.manager"
    _description = "FSM Notification Manager"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)
    notification_type = fields.Selection(
        [("email", "Email"), ("sms", "SMS"), ("push", "Push Notification")], string="Notification Type", required=True
    )
    recipient_ids = fields.Many2many(
        "res.partner",
        "fsm_notification_manager_res_partner_rel",
        "fsm_notification_manager_id",
        "res_partner_id",
        string="Recipients",
    )
    message = fields.Text(string="Message")
    scheduled_date = fields.Datetime(string="Scheduled Date")
    sent = fields.Boolean(string="Sent", default=False)


class NaidCertificate(models.Model):
    """NAID Certificate for compliance tracking"""

    _name = "naid.certificate"
    _description = "NAID Certificate"

    name = fields.Char(string="Certificate Number", required=True)
    active = fields.Boolean(default=True)
    issue_date = fields.Date(string="Issue Date", required=True)
    expiry_date = fields.Date(string="Expiry Date")
    certification_level = fields.Many2one("naid.certification.level", string="Certification Level")
    certified_by = fields.Many2one("res.partner", string="Certified By")
    certificate_type = fields.Selection(
        [("destruction", "Destruction"), ("storage", "Storage"), ("transport", "Transport")],
        string="Certificate Type",
        required=True,
    )


class ShreddingCertificate(models.Model):
    """Shredding Certificate for destruction verification"""

    _name = "shredding.certificate"
    _description = "Shredding Certificate"

    name = fields.Char(string="Certificate Number", required=True)
    active = fields.Boolean(default=True)
    destruction_date = fields.Datetime(string="Destruction Date", required=True)
    weight_destroyed = fields.Float(string="Weight Destroyed (lbs)")
    method_used = fields.Char(string="Destruction Method")
    witness_ids = fields.Many2many(
        "res.partner",
        "shredding_certificate_res_partner_rel",
        "shredding_certificate_id",
        "res_partner_id",
        string="Witnesses",
    )
    certificate_file = fields.Binary(string="Certificate File")
    certificate_filename = fields.Char(string="Certificate Filename")


class CertificateTemplateData(models.Model):
    """Certificate Template Data for generating certificates"""

    _name = "certificate.template.data"
    _description = "Certificate Template Data"

    name = fields.Char(string="Template Name", required=True)
    active = fields.Boolean(default=True)
    template_type = fields.Selection(
        [
            ("destruction", "Destruction Certificate"),
            ("storage", "Storage Certificate"),
            ("transport", "Transport Certificate"),
        ],
        string="Template Type",
        required=True,
    )
    template_content = fields.Text(string="Template Content")
    header_image = fields.Binary(string="Header Image")
    footer_text = fields.Text(string="Footer Text")


class FsmNotification(models.Model):
    """FSM Notification for field service communications"""

    _name = "fsm.notification"
    _description = "FSM Notification"

    name = fields.Char(string="Subject", required=True)
    active = fields.Boolean(default=True)
    notification_type = fields.Selection(
        [
            ("task_assigned", "Task Assigned"),
            ("task_completed", "Task Completed"),
            ("task_overdue", "Task Overdue"),
            ("service_reminder", "Service Reminder"),
        ],
        string="Notification Type",
        required=True,
    )
    recipient_id = fields.Many2one("res.partner", string="Recipient")
    message = fields.Text(string="Message")
    sent_date = fields.Datetime(string="Sent Date")
    read = fields.Boolean(string="Read", default=False)
