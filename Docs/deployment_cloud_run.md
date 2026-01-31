# Google Cloud Run Deployment Guide 🚀

Tämä opas neuvoo, kuinka `health_ai` backend julkaistaan Google Cloud Runiin.

## 1. Google Cloud Setup

1. **Luo Projekti:**
   - Mene [Google Cloud Consoleen](https://console.cloud.google.com/).
   - Luo uusi projekti (esim. `health-ai-prod`).
   - Kopioi **Project ID** talteen.

2. **Ota API:t käyttöön:**
   - Etsi ja "Enable" seuraavat API:t:
     - **Cloud Run API**
     - **Artifact Registry API**
     - **Secret Manager API**

3. **Luo Artifact Registry:**
   - Mene "Artifact Registry".
   - Luo uusi repository:
     - Name: `health-ai-repo`
     - Format: `Docker`
     - Region: `europe-north1` (tai haluamasi)

## 2. Service Account & Oikeudet

GitHub Actions tarvitsee oikeudet deployata.

1. **Luo Service Account:**
   - Mene "IAM & Admin" -> "Service Accounts".
   - Luo uusi: `github-deployer`.
   - Anna sille roolit:
     - **Cloud Run Admin**
     - **Service Account User**
     - **Artifact Registry Writer**
     - **Secret Manager Secret Accessor**

2. **Luo JSON Key:**
   - Klikkaa luotua service accountia -> Keys -> Add Key -> Create new key (JSON).
   - Lataa tiedosto koneellesi.

## 3. GitHub Secrets

Mene GitHub repositoriosi asetuksiin: `Settings` -> `Secrets and variables` -> `Actions`.

Lisää seuraavat **Repository Secrets**:

| Name | Value |
|------|-------|
| `GCP_PROJECT_ID` | Projektisi ID (esim. `health-ai-prod`) |
| `GCP_SA_KEY` | Lataamasi JSON-avaimen koko sisältö |

## 4. Secret Manager (Tuotannon salaisuudet)

Koska emme vie `.env` tiedostoa pilveen, tallennamme salaisuudet Google Secret Manageriin.

1. Mene "Security" -> "Secret Manager".
2. Luo seuraavat salaisuudet (samat kuin `.env.local` tiedostossa):
   - `GARMIN_EMAIL`
   - `GARMIN_PASSWORD`
   - `FIREBASE_CREDENTIALS` (Service account JSON base64-enkoodattuna tai tekstinä)
   - `ENCRYPTION_KEY`
   - `GEMINI_API_KEY`

---

## Julkaisu

Kun yllä olevat on tehty, **pushaa koodi main-haaraan**:

```bash
git add .
git commit -m "Setup Cloud Run deployment"
git push origin main
```

GitHub Action (`deploy-cloud-run.yml`) käynnistyy ja hoitaa loput! 🎉
