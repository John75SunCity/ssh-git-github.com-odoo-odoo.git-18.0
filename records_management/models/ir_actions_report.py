# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import Dict, Any
from odoo import models

class IrActionsReport(models.Model):
    """Extension for report actions to handle custom rendering contexts."""
    _inherit = 'ir.actions.report'

    def _get_report_values(self, docids, data=None) -> Dict[str, Any]:
        """
        Overrides to prepare values for report rendering.
        Enhances context for reception reports without docids.
        """
        values = super()._get_report_values(docids, data=data)
        report_name = 'stock.report_reception_report_label'
        if self.report_name == report_name and not docids:
    pass
            docids = data.get('docids', [])
            docs = self.env[self.model].browse(docids)
            values.update({
                'doc_ids': docids,
                'docs': docs,
            })
        return values
