from application.dto.quotation_request import QuotationRequest
from infrastructure.db.quotation_data_store import (
    save_generic_quotation_if_configured,
    save_kv_quotation_if_configured,
)


class QuotationDataStoreAdapter:
    def save_generic_run(self, request: QuotationRequest, output_filename: str, data: dict[str, list]) -> int | None:
        return save_generic_quotation_if_configured(request, output_filename, data)

    def save_kv_run(
        self,
        request: QuotationRequest,
        output_filename: str,
        codes: list,
        qty: list,
        prices: list,
    ) -> int | None:
        return save_kv_quotation_if_configured(request, output_filename, codes, qty, prices)

