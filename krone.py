"""
Mostek (adapter) – zachowuje stare API dla server.py.
"""

from application.use_cases.create_krone_quotation import CreateKroneQuotation

_use_case = CreateKroneQuotation()


def do_krone_quotation(filename, details):
    """Legacy entry point – deleguje do use case."""
    return _use_case.execute(filename, details)
