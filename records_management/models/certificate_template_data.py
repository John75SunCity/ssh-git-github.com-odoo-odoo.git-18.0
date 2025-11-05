# -*- coding: utf-8 -*-
"""
Certificate Template Data Module

Manages the templates used for generating various certificates, such as
Certificates of Destruction. This model allows for dynamic and customizable
certificate layouts.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, api, _

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


class CertificateTemplateData(models.Model):
    _name = 'certificate.template.data'
    _description = 'Certificate Template Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & CONFIGURATION
    # ============================================================================
    name = fields.Char(
        string='Template Name',
        required=True,
        tracking=True,
        help="A unique name for this certificate template."
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    active = fields.Boolean(string='Active', default=True)
    template_type = fields.Selection([
        ('destruction', 'Certificate of Destruction'),
        ('service', 'Service Confirmation'),
        ('compliance', 'Compliance Report'),
        ('other', 'Other')
    ], string='Template Type', required=True, default='destruction', tracking=True)
    template_format = fields.Selection([
        ('pdf', 'PDF'),
        ('html', 'HTML')
    ], string='Format', default='pdf', required=True)

    # ============================================================================
    # TEMPLATE CONTENT
    # ============================================================================
    header_text = fields.Html(
        string='Header Content',
        help="HTML content for the certificate header. Use placeholders for dynamic data."
    )
    body_template = fields.Html(
        string='Body Template',
        required=True,
        help="Main HTML body of the certificate. Use placeholders for dynamic data."
    )
    footer_text = fields.Html(
        string='Footer Content',
        help="HTML content for the certificate footer. Often used for legal text or page numbers."
    )
    logo_image = fields.Binary(
        string='Custom Logo',
        help="Upload a custom logo for this template. If empty, the company logo will be used."
    )

    # ============================================================================
    # COMPANY & AUTHORITY DETAILS
    # ============================================================================
    company_address = fields.Text(
        string='Company Address',
        compute='_compute_company_address',
        store=True,
        help="The address of the company, automatically populated."
    )
    certification_authority = fields.Char(
        string='Certification Authority',
        default="NAID AAA Certified",
        help="The authority or standard this certificate complies with (e.g., NAID AAA)."
    )

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'A certificate template with this name already exists for this company.'),
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('company_id')
    def _compute_company_address(self):
        """Computes the company address from the related partner."""
        for template in self:
            if template.company_id and template.company_id.partner_id:
                template.company_address = template.company_id.partner_id._display_address()
            else:
                template.company_address = ''

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Overrides create to handle potential placeholder names if needed."""
        # This is a placeholder for more complex logic if required in the future.
        # For now, we rely on the user to provide a meaningful name.
        return super().create(vals_list)
