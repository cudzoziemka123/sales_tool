from infrastructure.file_io.quotation_exporter import export_quotation


class QuotationExporterAdapter:
    """Adapter exporting quotation data to xlsx."""

    def export(self, data: dict, document: str) -> str:
        return export_quotation(data, document)

