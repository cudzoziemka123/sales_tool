"""
Mostek (adapter) – zachowuje stare API dla server.py.

Wszystka logika jest w application.use_cases.create_claas_quotation.
"""

from application.use_cases.create_claas_quotation import CreateClaasQuotation

_use_case = CreateClaasQuotation()


def do_claas_quotation(filename, details):
    """Legacy entry point – deleguje do use case."""
    return _use_case.execute(filename, details)
