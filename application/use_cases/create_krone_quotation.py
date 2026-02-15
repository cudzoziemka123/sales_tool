"""
Use case: quotation for Krone brand.
"""

from application.dto.quotation_request import QuotationRequest
from application.ports.quotation_ports import InputDataPort, PriceProviderPort, QuotationExporterPort


class CreateKroneQuotation:
    """Use case for creating Krone quotation."""

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
        """Run Krone quotation flow using injected ports."""
        filename = request.filename
        brand = request.brand
        data = self._input_data_port.prepare(filename, brand)
        self._price_provider_port.fill_prices(brand, data)
        document = filename.replace(".xlsx", "") if filename.endswith(".xlsx") else filename
        return self._exporter_port.export(data, document)

