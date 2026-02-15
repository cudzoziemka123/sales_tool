"""
Use case: quotation for Kverneland (KV).
"""

from application.dto.quotation_request import QuotationRequest
from application.ports.kv_quotation_ports import KvExporterPort, KvInputDataPort, KvPriceProviderPort


class CreateKvQuotation:
    """Use case for creating Kverneland quotation."""

    def __init__(
        self,
        input_data_port: KvInputDataPort,
        price_provider_port: KvPriceProviderPort,
        exporter_port: KvExporterPort,
    ):
        self._input_data_port = input_data_port
        self._price_provider_port = price_provider_port
        self._exporter_port = exporter_port

    def execute(self, request: QuotationRequest) -> str:
        """Run KV quotation flow using injected ports."""
        filename = request.filename
        search_payload = self._input_data_port.prepare(filename)
        codes_list, qty_list, price_list = self._price_provider_port.fetch(search_payload)
        document = filename.replace(".xlsx", "") if filename.endswith(".xlsx") else filename
        return self._exporter_port.export(codes_list, qty_list, price_list, document)

