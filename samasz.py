"""
Mostek (adapter) – zachowuje stare API dla server.py.
"""

from application.use_cases.create_samasz_quotation import CreateSamaszQuotation

_use_case = CreateSamaszQuotation()


def do_samasz_quotaion(filename, details):
    """Legacy entry point – deleguje do use case."""
    return _use_case.execute(filename, details)
