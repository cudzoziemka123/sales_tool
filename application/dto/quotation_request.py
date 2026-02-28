from dataclasses import dataclass

from application.errors import ValidationAppError


class InvalidQuotationRequestError(ValidationAppError):
    """Raised when quotation request payload cannot be parsed."""

    def __init__(self, message: str):
        super().__init__(message, code="ERR_INVALID_QUOTATION_REQUEST")


@dataclass(frozen=True)
class QuotationRequest:
    filename: str
    brand: str
    client_name: str
    markup: float
    discount: float
    euro: float
    for_client: bool
    # Keep in sync with brands visible in `templates/index.html`.
    # Brands without dedicated use case are handled by dispatcher fallback (Parts).
    SUPPORTED_BRANDS = {
        "claas",
        "samasz",
        "krone",
        "kv",
        "kverneland",
        "parts",
        "horsch",
        "amazone",
        "john deere",
    }

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

            brand_clean = str(brand).strip()
            brand_normalized = brand_clean.lower()
            markup_value = _to_float(markup)
            discount_value = _to_float(discount)
            euro_value = _to_float(euro)
            for_client_bool = for_client if isinstance(for_client, bool) else str(for_client).lower() == "true"

            if brand_normalized not in cls.SUPPORTED_BRANDS:
                raise InvalidQuotationRequestError(
                    f"Unsupported brand: {brand_clean}. "
                    f"Supported brands: {', '.join(sorted(cls.SUPPORTED_BRANDS))}"
                )
            if markup_value < 0:
                raise InvalidQuotationRequestError("Markup must be >= 0.")
            if discount_value < 0 or discount_value > 100:
                raise InvalidQuotationRequestError("Discount must be in range 0..100.")
            if euro_value <= 0:
                raise InvalidQuotationRequestError("Euro exchange rate must be > 0.")

            return cls(
                filename=str(filename),
                brand=brand_clean,
                client_name=str(client_name or "").strip(),
                markup=markup_value,
                discount=discount_value,
                euro=euro_value,
                for_client=for_client_bool,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidQuotationRequestError("Invalid quotation request values.") from exc
