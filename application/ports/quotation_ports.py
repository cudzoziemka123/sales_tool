from typing import Protocol


class InputDataPort(Protocol):
    """Loads and prepares quotation input data."""

    def prepare(self, filename: str, brand: str) -> dict:
        ...


class PriceProviderPort(Protocol):
    """Enriches quotation data with prices for given brand."""

    def fill_prices(self, brand: str, data: dict) -> None:
        ...


class QuotationExporterPort(Protocol):
    """Exports quotation to file and returns output filename."""

    def export(self, data: dict, document: str) -> str:
        ...

