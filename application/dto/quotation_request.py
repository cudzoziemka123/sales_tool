from dataclasses import dataclass


class InvalidQuotationRequestError(ValueError):
    """Raised when quotation request payload cannot be parsed."""


@dataclass(frozen=True)
class QuotationRequest:
    filename: str
    brand: str
    client_name: str
    markup: float
    discount: float
    euro: float
    for_client: bool

    @classmethod
    def from_raw(
        cls,
        filename: str,
        brand: str,
        markup: str | float,
        discount: str | float,
        euro: str | float,
        for_client: str | bool,
        client_name: str | None = None,
    ) -> "QuotationRequest":
        try:
            def _to_float(value: str | float) -> float:
                if isinstance(value, (int, float)):
                    return float(value)
                normalized = str(value).strip().replace(" ", "").replace(",", ".")
                return float(normalized)

            for_client_bool = for_client if isinstance(for_client, bool) else str(for_client).lower() == "true"
            return cls(
                filename=str(filename),
                brand=str(brand).strip(),
                client_name=str(client_name or "").strip(),
                markup=_to_float(markup),
                discount=_to_float(discount),
                euro=_to_float(euro),
                for_client=for_client_bool,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidQuotationRequestError("Invalid quotation request values.") from exc
