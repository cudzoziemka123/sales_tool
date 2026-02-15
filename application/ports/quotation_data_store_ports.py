from typing import Protocol

from application.dto.quotation_request import QuotationRequest


class QuotationDataStorePort(Protocol):
    def save_generic_run(self, request: QuotationRequest, output_filename: str, data: dict[str, list]) -> int | None:
        ...

    def save_kv_run(
        self,
        request: QuotationRequest,
        output_filename: str,
        codes: list,
        qty: list,
        prices: list,
    ) -> int | None:
        ...

