"""
Use case: quotation for brands available on 0parts.com.
"""

from application.dto.quotation_request import QuotationRequest
from application.ports.quotation_ports import InputDataPort, PriceProviderPort, QuotationExporterPort


class CreatePartsQuotation:
    """Use case for creating quotation via 0parts.com."""

    def __init__(
        self,
        input_data_port: InputDataPort,
        price_provider_port: PriceProviderPort,
        exporter_port: QuotationExporterPort,
    ):
        self._input_data_port = input_data_port
        self._price_provider_port = price_provider_port
        self._exporter_port = exporter_port

    def execute(self, request: QuotationRequest) -> str:
        """Run quotation flow using injected ports."""
        filename = request.filename
        brand = request.brand
        data = self._input_data_port.prepare(filename, brand)
        self._price_provider_port.fill_prices(brand, data)
        return self._exporter_port.export(data, filename)
