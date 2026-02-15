from infrastructure.file_interpreter import prepare_data


class QuotationInputDataAdapter:
    """Adapter loading and normalizing input data for quotation flow."""

    def prepare(self, filename: str, brand: str) -> dict:
        return prepare_data(filename, brand)


# Backward-compatible alias.
PartsInputDataAdapter = QuotationInputDataAdapter
