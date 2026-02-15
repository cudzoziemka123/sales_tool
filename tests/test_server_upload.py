import io
import importlib.util
import os
import unittest
from unittest.mock import patch

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
        self._uploaded_file = os.path.join("from_client", "test_upload.xlsx")

    def tearDown(self):
        if os.path.exists(self._uploaded_file):
            os.remove(self._uploaded_file)

    def _post_upload(self, markup: str = "10", discount: str = "0.2", euro: str = "4.3"):
        data = {"file": (io.BytesIO(b"dummy"), "test_upload.xlsx")}
        return self.client.post(
            f"/upload/Claas/{markup}/{discount}/{euro}/true",
            data=data,
            content_type="multipart/form-data",
        )

    def test_upload_returns_200_on_success(self):
        with patch.object(self.server._DISPATCHER, "execute_quotation", return_value="result.xlsx"):
            response = self._post_upload()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"result.xlsx", response.data)

    def test_upload_returns_400_on_invalid_request_payload(self):
        response = self._post_upload(markup="abc")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid quotation request values.", response.data)

    def test_upload_returns_500_on_missing_env_var(self):
        with patch.object(
            self.server._DISPATCHER,
            "execute_quotation",
            side_effect=self.MissingEnvVarError("Missing required environment variable: KV_LOGIN"),
        ):
            response = self._post_upload()

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Missing required environment variable: KV_LOGIN", response.data)


if __name__ == "__main__":
    unittest.main()

