"""
Insurer-specific policy parsers (STEP 8)

Each insurer has its own parser module implementing BasePolicyParser interface.
"""
from .samsung import SamsungPolicyParser
from .meritz import MeritzPolicyParser
from .db import DBPolicyParser

__all__ = [
    'SamsungPolicyParser',
    'MeritzPolicyParser',
    'DBPolicyParser',
]
