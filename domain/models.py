"""
Modele domenowe dla SalesTool.

Na razie proste szkielety – będą rozwijane w kolejnych krokach
refaktoryzacji (nie są jeszcze używane w kodzie).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Part:
    """Reprezentuje część zamienną w wycenie."""

    code: str
    quantity: int


@dataclass
class PartPrice:
    """Cena części dla jednej pozycji."""

    part_code: str
    base_price: float
    client_price: Optional[float] = None


@dataclass
class QuotationLine:
    """Linia w wycenie (kod + ilość + ceny)."""

    part: Part
    monthly_price: Optional[float] = None
    weekly_price: Optional[float] = None
    client_monthly_price: Optional[float] = None
    client_weekly_price: Optional[float] = None

