"""
Deprecated duplicate module placeholder.

The canonical implementation of `records.permanent.flag.wizard` lives in
`records_management/wizards/permanent_flag_wizard.py` (and manager variant in
`records_management/wizards/records_permanent_flag_wizard.py`).

This file intentionally defines no models to avoid duplicate registry entries.
"""

import logging

_logger = logging.getLogger(__name__)
_logger.debug("records_management.models.records_permanent_flag_wizard is deprecated; using wizards/permanent_flag_wizard instead")
