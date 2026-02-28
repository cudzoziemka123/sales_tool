# SalesTool

Narzędzie do tworzenia wycen części (Claas, Samasz, Krone, KV, Parts) z użyciem Flask + Selenium.

## Konfiguracja `.env`

Skopiuj `.env.example` do `.env` i uzupełnij dane:

- `FLASK_DEBUG`
- `POSTGRES_DSN` (opcjonalnie)
- `SAMASZ_COMPANY`, `SAMASZ_LOGIN`, `SAMASZ_PASSWORD`
- `KRONE_LOGIN`, `KRONE_PASSWORD`
- `KV_LOGIN`, `KV_PASSWORD`
- `PARTS_LOGIN`, `PARTS_PASSWORD`

## Healthcheck

- `GET /health` - szybkie sprawdzenie katalogów i brakujacych zmiennych srodowiskowych.
- `GET /health/deep` - dodatkowo test polaczenia z PostgreSQL i obecnosci cennika Claas.

## Error Matrix (skrót)

| Code | HTTP | Retryable | Znaczenie |
|---|---:|---:|---|
| `ERR_INVALID_QUOTATION_REQUEST` | 400 | no | Niepoprawne dane formularza lub pliku |
| `ERR_UPLOAD_TOO_LARGE` | 413 | no | Za duzy plik uploadu |
| `ERR_CONFIG` | 500 | no | Brak konfiguracji srodowiska |
| `ERR_STORAGE` | 500 | yes | Blad zapisu/odczytu danych |
| `ERR_NOT_FOUND` | 404 | no | Brak zasobu/pliku |
| `ERR_EXTERNAL_SERVICE` | 502 | yes | Blad integracji z zewnetrznym serwisem |
| `ERR_EXTERNAL_TIMEOUT` | 504 | yes | Timeout integracji zewnetrznej |
