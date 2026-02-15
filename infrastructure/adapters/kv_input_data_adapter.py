from infrastructure.file_interpreter import prepare_data_kv


class KvInputDataAdapter:
    """Adapter preparing input payload for KV ATP search."""

    def prepare(self, filename: str) -> str:
        return prepare_data_kv(filename)

