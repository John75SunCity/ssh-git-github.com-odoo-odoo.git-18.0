from . import models
from . import controllers
from . import report


def _post_init_hook(env):
    """Post-installation hook for Records Management module."""
    # Check if required dependencies are installed
    ir_module = env['ir.module.module']
    
    # List of required modules
    required_modules = ['stock', 'product', 'mail', 'portal']
    
    for module_name in required_modules:
        module = ir_module.search([('name', '=', module_name)])
        if not module or module.state != 'installed':
            # Log a warning instead of raising an error to allow installation
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(
                f"Required module '{module_name}' is not installed. "
                f"Please install it for full functionality."
            )
    
    # Initialize sequences if needed
    sequence_obj = env['ir.sequence']
    if not sequence_obj.search([('code', '=', 'records.box')]):
        sequence_obj.create({
            'name': 'Records Box Sequence',
            'code': 'records.box',
            'prefix': 'BOX',
            'padding': 4,
            'company_id': False,
        })
    
    if not sequence_obj.search([('code', '=', 'records.document')]):
        sequence_obj.create({
            'name': 'Records Document Sequence',
            'code': 'records.document',
            'prefix': 'DOC',
            'padding': 4,
            'company_id': False,
        })
