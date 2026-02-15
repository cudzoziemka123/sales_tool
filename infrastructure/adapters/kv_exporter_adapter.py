from infrastructure.file_io.quotation_exporter import export_quotation_from_lists


class KvExporterAdapter:
    """Adapter exporting KV quotation rows."""

    def export(self, codes: list, qty: list, prices: list, document: str) -> str:
        return export_quotation_from_lists(codes, qty, prices, document)

