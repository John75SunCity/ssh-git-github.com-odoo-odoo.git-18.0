from odoo import models, fields, api


class DestructionCertificateReport(models.AbstractModel):
    _name = 'report.rm.destruction_cert_template'
    _description = 'Destruction Certificate Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values for destruction certificate."""
        docs = self.env['destruction.certificate'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'destruction.certificate',
            'docs': docs,
            'data': data,
        }


class ReportDestructionCertificateTemplate(models.AbstractModel):
    _name = 'report.rm.report_destruction_cert_template'
    _description = 'Report Destruction Certificate Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values for destruction certificate template."""
        docs = self.env['destruction.certificate'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'destruction.certificate',
            'docs': docs,
            'data': data,
        }
