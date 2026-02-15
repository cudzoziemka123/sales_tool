from typing import Protocol

from application.dto.quotation_request import QuotationRequest


class QuotationUseCase(Protocol):
    """Unified use case contract for quotation flows."""

    def execute(self, request: QuotationRequest) -> str:
        ...

