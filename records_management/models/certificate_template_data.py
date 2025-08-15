# -*- coding: utf-8 -*-
"""
Certificate Template Data Model

Template data for generating destruction certificates.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CertificateTemplateData(models.Model):
    """Certificate Template Data"""

    _name = "certificate.template.data"
    _description = "Certificate Template Data"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Template Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the certificate template"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this template"
    )

    # ============================================================================
    # TEMPLATE CONFIGURATION
    # ============================================================================
    template_type = fields.Selection([
        ('destruction', 'Destruction Certificate'),
        ('storage', 'Storage Certificate'),
        ('transfer', 'Transfer Certificate'),
        ('audit', 'Audit Certificate'),
        ('compliance', 'Compliance Certificate')
    ], string='Template Type', required=True)

    template_format = fields.Selection([
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('docx', 'Word Document'),
        ('xlsx', 'Excel Spreadsheet')
    ], string='Format', default='pdf', required=True)

    # ============================================================================
    # TEMPLATE CONTENT
    # ============================================================================
    header_text = fields.Html(
        string="Header Text",
        help="Header content for the certificate"
    )

    body_template = fields.Html(
        string="Body Template",
        help="Main body template with placeholders"
    )

    footer_text = fields.Html(
        string="Footer Text",
        help="Footer content for the certificate"
    )

    # ============================================================================
    # BRANDING
    # ============================================================================
    logo_image = fields.Binary(
        string="Logo",
        help="Company logo for certificate"
    )

    company_address = fields.Text(
        string="Company Address",
        help="Company address to display"
    )

    certification_authority = fields.Char(
        string="Certification Authority",
        help="Name of certifying authority"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
