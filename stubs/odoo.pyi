# Type stubs for Odoo framework imports
# This provides type hints for common Odoo imports to suppress Pylance false positives

from typing import Any, Optional, Union, List, Dict, Callable, TypeVar, Generic
from .__init__ import *

# Common Odoo exceptions
class UserError(Exception):
    """User-facing error"""
    pass

class ValidationError(Exception):
    """Validation error"""
    pass

class AccessError(Exception):
    """Access permission error"""
    pass

class MissingError(Exception):
    """Record not found error"""
    pass

# HTTP framework
class Controller:
    """Base controller class"""
    pass

def route(route: str, **kwargs) -> Callable: ...

# Tools and utilities
def safe_eval(expr: str, globals_dict: Optional[Dict] = None, locals_dict: Optional[Dict] = None) -> Any: ...
def format_datetime(dt: Any, tz: Optional[str] = None) -> str: ...
def format_date(date: Any) -> str: ...
def format_amount(amount: float, currency: Any) -> str: ...

# Command utilities
def Command(action: str, *args) -> tuple: ...
