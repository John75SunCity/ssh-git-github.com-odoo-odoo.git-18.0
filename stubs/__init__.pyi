# Type stubs for Odoo framework
# This file provides basic type hints to suppress Pylance false positives

from typing import Any, Optional, Union, List, Dict, Callable, TypeVar, Generic

# Basic Odoo model types
ModelType = TypeVar('ModelType')

class BaseModel:
    """Base class for all Odoo models"""
    _name: str
    _description: str
    _inherit: Union[str, List[str]]
    _order: str
    _rec_name: str
    _table: str
    _auto: bool
    _log_access: bool
    _check_company_auto: bool
    _sql_constraints: List[tuple]
    _depends: Dict[str, Any]

    def __init__(self, *args, **kwargs) -> None: ...
    def create(self, vals_list: Union[Dict[str, Any], List[Dict[str, Any]]]) -> 'BaseModel': ...
    def write(self, vals: Dict[str, Any]) -> bool: ...
    def unlink(self) -> bool: ...
    def browse(self, ids: Union[int, List[int]]) -> 'BaseModel': ...
    def search(self, domain: List[List[Any]], **kwargs) -> 'BaseModel': ...
    def search_count(self, domain: List[List[Any]]) -> int: ...
    def read(self, fields: List[str]) -> List[Dict[str, Any]]: ...
    def read_group(self, domain: List[List[Any]], fields: List[str], groupby: List[str], **kwargs) -> List[Dict[str, Any]]: ...
    def name_get(self) -> List[tuple]: ...
    def name_search(self, name: str, **kwargs) -> List[tuple]: ...
    def copy(self, default: Optional[Dict[str, Any]] = None) -> 'BaseModel': ...
    def exists(self) -> 'BaseModel': ...
    def ensure_one(self) -> 'BaseModel': ...
    def filtered(self, func: Callable) -> 'BaseModel': ...
    def mapped(self, func: Callable) -> List[Any]: ...
    def sorted(self, key: Callable) -> 'BaseModel': ...

class Model(BaseModel):
    """Main Odoo Model class"""
    pass

class TransientModel(BaseModel):
    """Transient model for wizards and temporary data"""
    pass

class AbstractModel(BaseModel):
    """Abstract model for inheritance"""
    pass

# Field types
class Field:
    """Base field class"""
    def __init__(self, **kwargs) -> None: ...

class Char(Field):
    """Character field"""
    pass

class Text(Field):
    """Text field"""
    pass

class Integer(Field):
    """Integer field"""
    pass

class Float(Field):
    """Float field"""
    pass

class Boolean(Field):
    """Boolean field"""
    pass

class Date(Field):
    """Date field"""
    pass

class Datetime(Field):
    """Datetime field"""
    pass

class Binary(Field):
    """Binary field"""
    pass

class Html(Field):
    """HTML field"""
    pass

class Selection(Field):
    """Selection field"""
    pass

class Many2one(Field):
    """Many-to-one relationship field"""
    pass

class One2many(Field):
    """One-to-many relationship field"""
    pass

class Many2many(Field):
    """Many-to-many relationship field"""
    pass

class Monetary(Field):
    """Monetary field"""
    pass

class Reference(Field):
    """Reference field"""
    pass

class Json(Field):
    """JSON field"""
    pass

# API decorators
def api_model_create_multi(func: Callable) -> Callable: ...
def api_model(func: Callable) -> Callable: ...
def api_multi(func: Callable) -> Callable: ...
def api_one(func: Callable) -> Callable: ...
def api_constrains(*fields: str) -> Callable: ...
def api_depends(*fields: str) -> Callable: ...
def api_onchange(*fields: str) -> Callable: ...
def api_autovacuum(func: Callable) -> Callable: ...

# Environment and registry
class Environment:
    """Odoo environment"""
    user: 'BaseModel'
    company: 'BaseModel'
    context: Dict[str, Any]

    def __init__(self, cr, uid, context) -> None: ...
    def ref(self, xml_id: str) -> 'BaseModel': ...

# Common Odoo modules
api: Any
models: Any
fields: Any
exceptions: Any
tools: Any
http: Any
SUPERUSER_ID: int
uid: int
cr: Any
env: Environment

# Translation function
def _(msg: str) -> str: ...
