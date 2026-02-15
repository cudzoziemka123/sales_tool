import unittest

from application.dto.quotation_request import InvalidQuotationRequestError, QuotationRequest


class QuotationRequestTests(unittest.TestCase):
    def test_from_raw_parses_values(self):
        request = QuotationRequest.from_raw(
            filename="doc.xlsx",
            brand="Claas",
            markup="12.5",
            discount="0.1",
            euro="4.2",
            for_client="true",
        )

        self.assertEqual(request.filename, "doc.xlsx")
        self.assertEqual(request.brand, "Claas")
        self.assertEqual(request.markup, 12.5)
        self.assertEqual(request.discount, 0.1)
        self.assertEqual(request.euro, 4.2)
        self.assertTrue(request.for_client)

    def test_from_raw_raises_on_invalid_numbers(self):
        with self.assertRaises(InvalidQuotationRequestError):
            QuotationRequest.from_raw(
                filename="doc.xlsx",
                brand="Krone",
                markup="abc",
                discount="0.1",
                euro="4.2",
                for_client="false",
            )


if __name__ == "__main__":
    unittest.main()
