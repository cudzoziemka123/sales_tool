from functools import lru_cache

from application.use_cases.create_claas_quotation import CreateClaasQuotation
from application.use_cases.create_krone_quotation import CreateKroneQuotation
from application.use_cases.create_kv_quotation import CreateKvQuotation
from application.use_cases.create_parts_quotation import CreatePartsQuotation
from application.use_cases.create_samasz_quotation import CreateSamaszQuotation
from application.use_cases.quotation_dispatcher import QuotationDispatcher
from infrastructure.adapters.claas_price_provider_adapter import ClaasPriceProviderAdapter
from infrastructure.adapters.krone_price_provider_adapter import KronePriceProviderAdapter
from infrastructure.adapters.kv_exporter_adapter import KvExporterAdapter
from infrastructure.adapters.kv_input_data_adapter import KvInputDataAdapter
from infrastructure.adapters.kv_price_provider_adapter import KvPriceProviderAdapter
from infrastructure.adapters.quotation_data_store_adapter import QuotationDataStoreAdapter
from infrastructure.adapters.parts_input_data_adapter import QuotationInputDataAdapter
from infrastructure.adapters.parts_price_provider_adapter import PartsPriceProviderAdapter
from infrastructure.adapters.quotation_exporter_adapter import QuotationExporterAdapter
from infrastructure.adapters.samasz_price_provider_adapter import SamaszPriceProviderAdapter


def build_quotation_dispatcher() -> QuotationDispatcher:
    """Compose use cases with infrastructure adapters for HTTP layer."""
    input_data_adapter = QuotationInputDataAdapter()
    exporter_adapter = QuotationExporterAdapter()
    data_store_adapter = QuotationDataStoreAdapter()

    default_use_case = CreatePartsQuotation(
        input_data_port=input_data_adapter,
        price_provider_port=PartsPriceProviderAdapter(),
        exporter_port=exporter_adapter,
        data_store_port=data_store_adapter,
    )
    use_cases = {
        "Samasz": CreateSamaszQuotation(
            input_data_port=input_data_adapter,
            price_provider_port=SamaszPriceProviderAdapter(),
            exporter_port=exporter_adapter,
            data_store_port=data_store_adapter,
        ),
        "Kverneland": CreateKvQuotation(
            input_data_port=KvInputDataAdapter(),
            price_provider_port=KvPriceProviderAdapter(),
            exporter_port=KvExporterAdapter(),
            data_store_port=data_store_adapter,
        ),
        "Claas": CreateClaasQuotation(
            input_data_port=input_data_adapter,
            price_provider_port=ClaasPriceProviderAdapter(),
            exporter_port=exporter_adapter,
            data_store_port=data_store_adapter,
        ),
        "Krone": CreateKroneQuotation(
            input_data_port=input_data_adapter,
            price_provider_port=KronePriceProviderAdapter(),
            exporter_port=exporter_adapter,
            data_store_port=data_store_adapter,
        ),
    }
    return QuotationDispatcher(use_cases=use_cases, default_use_case=default_use_case)


@lru_cache(maxsize=1)
def get_dispatcher() -> QuotationDispatcher:
    return build_quotation_dispatcher()
