"""Application-level dispatcher for quotation use cases."""

from application.dto.quotation_request import QuotationRequest
from application.use_cases.contracts import QuotationUseCase


class QuotationDispatcher:
    """Selects and runs proper use case based on brand."""

    def __init__(self, use_cases: dict[str, QuotationUseCase], default_use_case: QuotationUseCase):
        self._use_cases = use_cases
        self._default_use_case = default_use_case

    def execute_quotation(self, request: QuotationRequest) -> str:
        use_case = self._use_cases.get(request.brand, self._default_use_case)
        return use_case.execute(request)
