from typing import Protocol


class KvInputDataPort(Protocol):
    """Loads and prepares search payload for KV flow."""

    def prepare(self, filename: str) -> str:
        ...


class KvPriceProviderPort(Protocol):
    """Fetches quotation rows for KV flow."""

    def fetch(self, search_payload: str) -> tuple[list, list, list]:
        ...


class KvExporterPort(Protocol):
    """Exports KV quotation rows to file and returns filename."""

    def export(self, codes: list, qty: list, prices: list, document: str) -> str:
        ...

