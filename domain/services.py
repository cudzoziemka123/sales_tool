"""
Usługi domenowe – czysta logika biznesowa bez I/O.

Na tym etapie przenosimy tutaj logikę z `file_interpeter.py`,
tak aby:
- odczyt Excela (I/O) został w warstwie infrastruktury,
- a przygotowanie danych i wyliczanie cen było w domenie.
"""

from typing import Any, Dict, List, Tuple


def add_zeros_for_horsch(code: str) -> str:
    """
    Normalizuje kod części Horsch, dodając zera wiodące
    tak jak w dotychczasowej implementacji.
    """
    if len(code) < 7:
        new_code = code.rjust(8 - len(code) + len(code), "0")
    else:
        new_code = code
    return new_code


def reduce_floats(el: Dict[str, Any]) -> Dict[str, str]:
    """
    Usuwa część po kropce z wartości w kolumnach Code/Qty
    (np. z Excela, gdzie wartości mogą być floatami).
    """
    code_str = str(el["Code"]).split(".")[0]
    qty_str = str(el["Qty"]).split(".")[0]
    return {"code_str": code_str, "qty_str": qty_str}


def _normalize_code_and_qty(el: Dict[str, Any], brand: str) -> Tuple[str, str]:
    """
    Wewnętrzna funkcja domenowa, która na podstawie brandu
    zwraca przygotowany kod i ilość jako stringi.
    """
    if brand != "Samasz":
        reduced_data_el = reduce_floats(el)
        qty_str = reduced_data_el["qty_str"]

        if brand == "Horsch":
            code_str = add_zeros_for_horsch(reduced_data_el["code_str"])
        else:
            code_str = reduced_data_el["code_str"]
    else:
        code_str = str(el["Code"])
        qty_str = str(el["Qty"])

    return str(code_str), qty_str


def prepare_data_from_records(
    records: List[Dict[str, Any]], brand: str
) -> Dict[str, list]:
    """
    Przygotowuje strukturę `data` na podstawie rekordów wczytanych z Excela.

    Ta funkcja odpowiada za to, co wcześniej działo się w `prepare_data`
    po wywołaniu `load_data_from_excel`.
    """
    data = {
        "codes": [],
        "qty": [],
        "monthly_prices": [],
        "weekly_prices": [],
        "samasz_codes": [],
        "prices": [],
        "prices_for_client": [],
        "prices_for_client_weekly": [],
        "prices_for_client_monthly": [],
    }

    for el in records:
        code_str, qty_str = _normalize_code_and_qty(el, brand)
        data["codes"].append(code_str)
        data["qty"].append(qty_str)

    return data


def price_for_client(price: float, discount: float, markup: float, euro: float) -> float:
    """
    Logika przeliczania ceny dla klienta – przeniesiona 1:1 z `file_interpeter.py`.
    """
    price_with_discount = price - price * discount
    euro_price = price_with_discount / euro
    price_with_markup = euro_price * ((100 + markup) / 100)
    return round(price_with_markup, 2)
