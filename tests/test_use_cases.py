import unittest

from application.dto.quotation_request import QuotationRequest
from application.use_cases.create_claas_quotation import CreateClaasQuotation
from application.use_cases.create_krone_quotation import CreateKroneQuotation
from application.use_cases.create_kv_quotation import CreateKvQuotation
from application.use_cases.create_parts_quotation import CreatePartsQuotation
from application.use_cases.create_samasz_quotation import CreateSamaszQuotation


class _InputDataPortStub:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def prepare(self, filename, brand):
        self.calls.append((filename, brand))
        return self.data


class _PriceProviderPortStub:
    def __init__(self):
        self.calls = []

    def fill_prices(self, brand, data):
        self.calls.append((brand, data))


class _ExporterPortStub:
    def __init__(self, result_filename):
        self.result_filename = result_filename
        self.calls = []

    def export(self, data, document):
        self.calls.append((data, document))
        return self.result_filename


class _KvInputPortStub:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def prepare(self, filename):
        self.calls.append(filename)
        return self.payload


class _KvPriceProviderStub:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def fetch(self, search_payload):
        self.calls.append(search_payload)
        return self.result


class _KvExporterStub:
    def __init__(self, result_filename):
        self.result_filename = result_filename
        self.calls = []

    def export(self, codes, qty, prices, document):
        self.calls.append((codes, qty, prices, document))
        return self.result_filename


class _ClaasPriceProviderStub:
    def __init__(self):
        self.calls = []

    def fill_prices(self, data, request):
        self.calls.append((data, request))


class UseCaseTests(unittest.TestCase):
    def test_parts_use_case_uses_ports(self):
        data = {"codes": ["A1"]}
        input_port = _InputDataPortStub(data)
        price_port = _PriceProviderPortStub()
        exporter = _ExporterPortStub("out.xlsx")
        use_case = CreatePartsQuotation(input_port, price_port, exporter)

        request = QuotationRequest.from_raw(
            filename="doc.xlsx",
            brand="Krone",
            markup="10",
            discount="0.2",
            euro="4.3",
            for_client="true",
        )
        result = use_case.execute(request)

        self.assertEqual(result, "out.xlsx")
        self.assertEqual(input_port.calls, [("doc.xlsx", "Krone")])
        self.assertEqual(price_port.calls, [("Krone", data)])
        self.assertEqual(exporter.calls, [(data, "doc.xlsx")])

    def test_samasz_use_case_uses_ports(self):
        data = {"codes": ["S1"]}
        input_port = _InputDataPortStub(data)
        price_port = _PriceProviderPortStub()
        exporter = _ExporterPortStub("sam.xlsx")
        use_case = CreateSamaszQuotation(input_port, price_port, exporter)

        request = QuotationRequest.from_raw(
            filename="sam_doc.xlsx",
            brand="Krone",
            markup="10",
            discount="0.2",
            euro="4.3",
            for_client="true",
        )
        result = use_case.execute(request)

        self.assertEqual(result, "sam.xlsx")
        self.assertEqual(input_port.calls, [("sam_doc.xlsx", "Krone")])
        self.assertEqual(price_port.calls, [("Krone", data)])
        self.assertEqual(exporter.calls, [(data, "sam_doc.xlsx")])

    def test_krone_use_case_strips_xlsx_suffix(self):
        data = {"codes": ["K1"]}
        input_port = _InputDataPortStub(data)
        price_port = _PriceProviderPortStub()
        exporter = _ExporterPortStub("krone_out.xlsx")
        use_case = CreateKroneQuotation(input_port, price_port, exporter)

        request = QuotationRequest.from_raw(
            filename="krone_doc.xlsx",
            brand="Krone",
            markup="10",
            discount="0.2",
            euro="4.3",
            for_client="true",
        )
        result = use_case.execute(request)

        self.assertEqual(result, "krone_out.xlsx")
        self.assertEqual(exporter.calls, [(data, "krone_doc")])

    def test_kv_use_case_uses_kv_ports(self):
        input_port = _KvInputPortStub("payload")
        price_port = _KvPriceProviderStub((["C1"], ["2"], ["100"]))
        exporter = _KvExporterStub("kv_out.xlsx")
        use_case = CreateKvQuotation(input_port, price_port, exporter)

        request = QuotationRequest.from_raw(
            filename="kv_doc.xlsx",
            brand="Kverneland",
            markup="10",
            discount="0.2",
            euro="4.3",
            for_client="true",
        )
        result = use_case.execute(request)

        self.assertEqual(result, "kv_out.xlsx")
        self.assertEqual(input_port.calls, ["kv_doc.xlsx"])
        self.assertEqual(price_port.calls, ["payload"])
        self.assertEqual(exporter.calls, [(["C1"], ["2"], ["100"], "kv_doc")])

    def test_claas_use_case_passes_request_to_price_provider(self):
        data = {"codes": ["CL1"]}
        input_port = _InputDataPortStub(data)
        price_port = _ClaasPriceProviderStub()
        exporter = _ExporterPortStub("claas_out.xlsx")
        use_case = CreateClaasQuotation(input_port, price_port, exporter)

        request = QuotationRequest.from_raw(
            filename="claas_doc.xlsx",
            brand="Claas",
            markup="10",
            discount="0.2",
            euro="4.3",
            for_client="true",
        )
        result = use_case.execute(request)

        self.assertEqual(result, "claas_out.xlsx")
        self.assertEqual(input_port.calls, [("claas_doc.xlsx", "Claas")])
        self.assertEqual(price_port.calls, [(data, request)])
        self.assertEqual(exporter.calls, [(data, "claas_doc.xlsx")])


if __name__ == "__main__":
    unittest.main()
