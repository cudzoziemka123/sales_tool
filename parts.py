"""
Mostek (adapter) – zachowuje stare API dla server.py.
"""

from application.use_cases.create_parts_quotation import CreatePartsQuotation

_use_case = CreatePartsQuotation()


def do_another_quotation(filename, details):
    """Legacy entry point – deleguje do use case."""
    return _use_case.execute(filename, details)
