# Julkaisuopas (Deployment Guide) 🚀

> **Huom:** Täydellisen, haettavan dokumentaation löydät [Dokumentaatiosivustoltamme](https://Samih.github.io/health_ai/).

## Ympäristöt

Tuemme kolmea standardia ympäristöä:

### 1. Kehitys (Development - Local)
- **Käyttötapaus:** Paikallinen koodaus ja testaus.
- **Konfiguraatio:** `APP_ENV=development`
- **Ominaisuudet:**
  - Debug-tila: PÄÄLLÄ (Yksityiskohtaiset virhelokit)
  - CORS: Sallii localhostin
  - Reload: Hot reloading käytössä
- **Komento:**
  ```bash
  docker-compose up
  ```

### 2. Tuotanto (Production)
- **Käyttötapaus:** Julkinen käyttö.
- **Konfiguraatio:** `APP_ENV=production`
- **Ominaisuudet:**
  - Debug-tila: POIS (Yleiset virheilmoitukset)
  - CORS: Tiukka (vaatii `FRONTEND_URL`:n)
  - Reload: Ei käytössä
- **Komento:**
  ```bash
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  ```

### 3. Staging (Valinnainen)
- **Konfiguraatio:** `APP_ENV=staging`
- Jäljittelee tuotantoa, mutta saattaa käyttää testitietokantaa.

## Konfigurointi

Asetuksia hallitaan tiedostossa [`backend/config.py`](../backend/config.py).  
Hierarkiaa käsittelee Pydantic: `Settings` -> `DevelopmentSettings` / `ProductionSettings`.

## Tietoturvahuomiot
- Varmista, että `.env` tiedostoa **EI KOSKAAN** tallenneta Gitiin.
- Tuotannossa aseta `FRONTEND_URL` vastaamaan oikeaa domainia (esim. `https://healthai.app`).
