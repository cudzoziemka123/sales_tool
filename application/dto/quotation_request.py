from dataclasses import dataclass


class InvalidQuotationRequestError(ValueError):
    """Raised when quotation request payload cannot be parsed."""


@dataclass(frozen=True)
class QuotationRequest:
    filename: str
    brand: str
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
    ) -> "QuotationRequest":
        try:
            for_client_bool = for_client if isinstance(for_client, bool) else str(for_client).lower() == "true"
            return cls(
                filename=str(filename),
                brand=str(brand).strip(),
                markup=float(markup),
                discount=float(discount),
                euro=float(euro),
                for_client=for_client_bool,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidQuotationRequestError("Invalid quotation request values.") from exc
