"""
Modele domenowe dla SalesTool.

Na razie proste szkielety – będą rozwijane w kolejnych krokach
refaktoryzacji (nie są jeszcze używane w kodzie).
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime

from click import File


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


@dataclass
class Contrahent:
    """Reprezentuje kontrahenta."""
    id: str
    name: str
    address: str
    nip: str
    email: str
    phone: str
    website: str
    notes: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Client (Contrahent):
    """Reprezentuje klienta."""
    id: str


@dataclass
class Supplier (Contrahent):
    """Reprezentuje dostawcę."""
    id: str


@dataclass
class Quotation:
    """Reprezentuje wycenę."""
    id: str
    client: Client
    supplier: Supplier
    brand: str
    lines: List[QuotationLine]
    total_price: float
    total_price_for_client: float


@dataclass
class Order:
    """Reprezentuje zamówienie."""
    id: str
    quotation: List[Quotation]
    client: Client
    lines: List[QuotationLine]
    total_price: float
    total_price_for_client: float


@dataclass
class Document:
    """Reprezentuje dokument."""
    id: str
    name: str
    path: str
    client: Client
    created_at: datetime
    updated_at: datetime


@dataclass
class Contract(Document):
    """Reprezentuje umowę."""
    number: str
    date: date
    expiration_date: date
    file: File


@dataclass
class Invoice(Document):
    """Reprezentuje fakturę."""
    number: str
    date: date
    client: Client
    order: Order
    file: File


@dataclass
class CMR(Document):
    """Reprezentuje CMR."""
    number: str
    date: date
    client: Client
    file: File


@dataclass
class ProformaInvoice(Document):
    """Reprezentuje fakturę proforma."""
    number: str
    date: date
    client: Client
    order: Order
    file: File


@dataclass
class Task:
    """Reprezentuje zadanie."""
    id: str
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Loading:
    """Reprezentuje ładowanie."""
    id: str
    client: Client
    date: date
    documents: List[Document]


@dataclass
class Storage:
    """Reprezentuje magazyn."""
    id: str
    name: str
