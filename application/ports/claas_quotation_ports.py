from typing import Protocol

from application.dto.quotation_request import QuotationRequest
from application.ports.quotation_ports import QuotationExporterPort


class ClaasInputDataPort(Protocol):
    """Loads and prepares Claas input data."""

    def prepare(self, filename: str, brand: str) -> dict:
        ...


class ClaasPriceProviderPort(Protocol):
    """Fills Claas prices into quotation data."""

    def fill_prices(self, data: dict, request: QuotationRequest) -> None:
        ...


__all__ = ["ClaasInputDataPort", "ClaasPriceProviderPort", "QuotationExporterPort"]

