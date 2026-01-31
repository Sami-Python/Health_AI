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

Asetuksia hallitaan tiedostossa [`backend/config.py`](https://github.com/Samih/health_ai/blob/main/backend/config.py).  
Hierarkiaa käsittelee Pydantic: `Settings` -> `DevelopmentSettings` / `ProductionSettings`.

## Tietoturvahuomiot
- Varmista, että `.env` tiedostoa **EI KOSKAAN** tallenneta Gitiin.
- Tuotannossa aseta `FRONTEND_URL` vastaamaan oikeaa domainia (esim. `https://healthai.app`).

## 4. Pilvijulkaisu (Cloud Run) ☁️

Tämä osio neuvoo, kuinka `health_ai` backend julkaistaan Google Cloud Runiin.

### 4.1 Esivaatimukset (Google Cloud)

1.  **Projekti:** Luo projekti Google Cloud Consolessa ja ota talteen `Project ID`.
2.  **API:t:** Ota käyttöön:
    *   Cloud Run API
    *   Artifact Registry API
    *   Secret Manager API
3.  **Artifact Registry:** Luo repository nimeltä `health-ai-repo` (Format: Docker, Region: europe-north1).
4.  **Service Account:**
    *   Luo `github-deployer` oikeuksilla: Cloud Run Admin, Service Account User, Artifact Registry Writer, Secret Manager Secret Accessor.
    *   Luo JSON-avain ja lataa se.
5.  **Secrets:** Tallenna Secret Manageriin: `GARMIN_EMAIL`, `GARMIN_PASSWORD`, `FIREBASE_CREDENTIALS`, `GEMINI_API_KEY`, `ENCRYPTION_KEY`.

### 4.2 GitHub Konfiguraatio

Lisää Repository Secrets (`Settings` -> `Secrets`):
*   `GCP_PROJECT_ID`: Projektisi ID
*   `GCP_SA_KEY`: Service Account JSON-avaimen sisältö

### 4.3 Julkaisu

Julkaisu tapahtuu automaattisesti, kun koodi työnnetään `main`-haaraan:

```bash
git push origin main
```

GitHub Action `deploy-cloud-run.yml`:
1.  Rakentaa Docker-imagen.
2.  Työntää sen Artifact Registryyn.
3.  Deployaa Cloud Runiin ja kytkee salaisuudet.

