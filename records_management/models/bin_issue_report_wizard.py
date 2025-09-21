"""
Deprecated duplicate module placeholder.

The canonical implementation of `bin.issue.report.wizard` lives in
`records_management/wizards/bin_issue_report_wizard.py`.

This file remains only to avoid accidental imports; it intentionally defines
no Odoo models. Do not add model classes here.
"""

import logging

_logger = logging.getLogger(__name__)
_logger.debug("records_management.models.bin_issue_report_wizard is deprecated; using wizards/bin_issue_report_wizard instead")
