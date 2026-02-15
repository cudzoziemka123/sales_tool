"""
Use case: quotation for Claas brand.
"""

from application.dto.quotation_request import QuotationRequest
from application.ports.claas_quotation_ports import ClaasInputDataPort, ClaasPriceProviderPort, QuotationExporterPort
from application.ports.quotation_data_store_ports import QuotationDataStorePort


class CreateClaasQuotation:
    """Use case for creating Claas quotation."""

    def __init__(
        self,
        input_data_port: ClaasInputDataPort,
        price_provider_port: ClaasPriceProviderPort,
        exporter_port: QuotationExporterPort,
        data_store_port: QuotationDataStorePort,
    ):
        self._input_data_port = input_data_port
        self._price_provider_port = price_provider_port
        self._exporter_port = exporter_port
        self._data_store_port = data_store_port

    def execute(self, request: QuotationRequest) -> str:
        """Run Claas quotation flow using injected ports."""
        filename = request.filename
        data = self._input_data_port.prepare(filename, request.brand)
        self._price_provider_port.fill_prices(data, request)
        output_filename = self._exporter_port.export(data, filename)
        self._data_store_port.save_generic_run(request, output_filename, data)
        return output_filename

