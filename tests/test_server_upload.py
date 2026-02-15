import io
import importlib.util
import unittest
from unittest.mock import patch

import pandas as pd

FLASK_AVAILABLE = importlib.util.find_spec("flask") is not None


@unittest.skipUnless(FLASK_AVAILABLE, "Flask is not installed in current environment.")
class ServerUploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server

        from infrastructure.config.env_loader import MissingEnvVarError

        cls.server = server
        cls.MissingEnvVarError = MissingEnvVarError

    def setUp(self):
        self.server.app.testing = True
        self.client = self.server.app.test_client()

    @staticmethod
    def _xlsx_bytes(columns: dict[str, list]):
        buffer = io.BytesIO()
        pd.DataFrame(columns).to_excel(buffer, index=False)
        return buffer.getvalue()

    def _post_upload(
        self,
        markup: str = "10",
        discount: str = "0.2",
        euro: str = "4.3",
        file_columns: dict[str, list] | None = None,
    ):
        payload_columns = file_columns or {"Code": ["A1"], "Qty": [1]}
        data = {
            "brand": "Claas",
            "markup": markup,
            "discount": discount,
            "euro": euro,
            "for_client": "true",
            "client_name": "Test Client",
            "file": (io.BytesIO(self._xlsx_bytes(payload_columns)), "test_upload.xlsx"),
        }
        return self.client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )

    def test_upload_returns_200_on_success(self):
        with (
            patch.object(self.server, "store_file_if_configured", return_value=True),
            patch.object(self.server._DISPATCHER, "execute_quotation", return_value="result.xlsx"),
            patch.object(self.server, "get_latest_run_id_by_output_filename_if_configured", return_value=123),
        ):
            response = self._post_upload()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/quotations/123/download", response.data)

    def test_upload_returns_400_on_invalid_request_payload(self):
        with patch.object(self.server, "store_file_if_configured", return_value=True):
            response = self._post_upload(markup="abc")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid quotation request values.", response.data)

    def test_upload_returns_500_on_missing_env_var(self):
        with (
            patch.object(self.server, "store_file_if_configured", return_value=True),
            patch.object(
                self.server._DISPATCHER,
                "execute_quotation",
                side_effect=self.MissingEnvVarError("Missing required environment variable: KV_LOGIN"),
            ),
        ):
            response = self._post_upload()

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Missing required environment variable: KV_LOGIN", response.data)

    def test_upload_returns_400_when_required_columns_missing(self):
        with patch.object(self.server, "store_file_if_configured", return_value=True):
            response = self._post_upload(file_columns={"Code": ["A1"]})

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing required columns: Qty", response.data)


if __name__ == "__main__":
    unittest.main()
