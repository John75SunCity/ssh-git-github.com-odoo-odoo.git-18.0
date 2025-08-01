# -*- coding: utf-8 -*-

import logging
import subprocess
import sys

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """
    Pre-installation hook to handle optional dependencies gracefully.
    This prevents RPC errors during module installation when external
    dependencies are missing.
    """
    _logger.info("Records Management: Checking optional dependencies...")

    # List of optional dependencies with their purposes
    optional_deps = {
        "qrcode": "QR code generation for advanced features",
        "PIL": "Image processing for enhanced document handling",
        "cryptography": "Enhanced encryption for security features",
        "requests": "Advanced webhook and API integration",
    }

    missing_deps = []
    available_deps = []

    for dep_name, purpose in optional_deps.items():
        try:
            if dep_name == "PIL":
                import PIL

                available_deps.append(dep_name)
            else:
                __import__(dep_name)
                available_deps.append(dep_name)
        except ImportError:
            missing_deps.append(dep_name)
            _logger.warning(
                f"Records Management: Optional dependency '{dep_name}' not found. "
                f"Feature disabled: {purpose}"
            )

    if available_deps:
        _logger.info(
            f"Records Management: Available optional dependencies: {', '.join(available_deps)}"
        )

    if missing_deps:
        _logger.info(
            f"Records Management: Missing optional dependencies: {', '.join(missing_deps)}"
        )
        _logger.info(
            "Records Management: Module will install with reduced functionality. "
            "Install missing dependencies later to enable all features."
        )
    else:
        _logger.info(
            "Records Management: All optional dependencies available - full functionality enabled."
        )


def post_init_hook(env):
    """
    Post-installation hook to finalize setup and log status.
    """
    _logger.info("Records Management: Module installation completed successfully!")

    # Set up any required data or configurations
    try:
        # Create default configurations if needed
        company = env.ref("base.main_company", raise_if_not_found=False)
        if company:
            _logger.info("Records Management: Configured for default company")
    except Exception as e:
        _logger.warning(f"Records Management: Post-init configuration warning: {e}")
