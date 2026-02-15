"""
Mostek (adapter) – zachowuje stare API dla server.py.
"""

from application.use_cases.create_kv_quotation import CreateKvQuotation

_use_case = CreateKvQuotation()


def do_kv_quotation(filename, details):
    """Legacy entry point – deleguje do use case."""
    return _use_case.execute(filename, details)
