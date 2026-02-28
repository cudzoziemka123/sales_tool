"""
Use case: quotation for Kverneland (KV).
"""

from application.dto.quotation_request import QuotationRequest
from application.ports.kv_quotation_ports import KvExporterPort, KvInputDataPort, KvPriceProviderPort
from application.ports.quotation_data_store_ports import QuotationDataStorePort
from domain.services import apply_client_prices_to_list


class CreateKvQuotation:
    """Use case for creating Kverneland quotation."""

    def __init__(
        self,
        input_data_port: KvInputDataPort,
        price_provider_port: KvPriceProviderPort,
        exporter_port: KvExporterPort,
        data_store_port: QuotationDataStorePort,
    ):
        self._input_data_port = input_data_port
        self._price_provider_port = price_provider_port
        self._exporter_port = exporter_port
        self._data_store_port = data_store_port

    def execute(self, request: QuotationRequest) -> str:
        """Run KV quotation flow using injected ports."""
        filename = request.filename
        search_payload = self._input_data_port.prepare(filename)
        codes_list, qty_list, price_list, client_prices = self._price_provider_port.fetch(search_payload)
        if request.for_client and client_prices is None:
            client_prices = apply_client_prices_to_list(
                price_list,
                discount=request.discount,
                markup=request.markup,
                euro=request.euro,
            )
        document = filename.replace(".xlsx", "") if filename.endswith(".xlsx") else filename
        output_filename = self._exporter_port.export(
            codes_list, qty_list, price_list, client_prices, document
        )
        self._data_store_port.save_kv_run(
            request, output_filename, codes_list, qty_list, price_list, client_prices
        )
        return output_filename

