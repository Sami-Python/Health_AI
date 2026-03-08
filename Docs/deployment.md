# Julkaisuopas (Deployment Guide)

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

#### Vianetsintä (Troubleshooting)
Jos kohtaat ongelmia välimuistien tai riippuvuuksien kanssa (esim. Tailwind ei päivity), aja frontend-kansiossa:
```bash
npm run fix
```
Tämä komento tuhoaa turvallisesti `node_modules`, `.next` (build cache) ja `package-lock.json` -tiedostot ja asentaa riippuvuudet puhtaalta pöydältä.

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

## 4. Pilvijulkaisu (Cloud Run)

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

### 4.4 Huomioitavaa pilviarkkitehtuurissa (Stateless)

Google Cloud Run on rakenteeltaan "Stateless" (tilaton). Tämä tarkoittaa sitä, että aina kun palvelin nukahtaa (esim. 5 minuuttia ilman liikennettä) ja skaalautuu nollaan, tai käynnistää uusia rinnakkaisia instansseja ruuhkassa, **kaikki väliaikaiset tiedostot pyyhkiytyvät pois**.

* **`backend/data/` -kansio:** Älä oleta, että CSV-tiedostot (kuten `garmin_hr_timeseries.csv`) tai ML-mallit (`xgb_model.pkl`) säilyvät pyyntöjen välillä. 
* **Korjaus ja ratkaisut:** Ohjelma on koodattu siten, että jos se ei löydä tiedostoja nollaantumisen jälkeen, se käynnistää laajemman historian "fallback" haun (esimerkiksi vain 7 päivää "Quick Sync" -moodissa muistin säästämiseksi verrattuna 360-päivän "Full Trainiin"). Tulevaisuudessa, mikäli haluat täysin persistentin datan, sinun tulee hyödyntää tietokantaa (kuten Firestore tai BigQuery) CSV-tiedostojen sijaan.

---

## 5. Mobiilisovelluksen Julkaisu ja Päivitys (Android)

### 5.1 Päivitys Play Kauppaan (Best Practices)

Kun sovellusta päivitetään jatkossa Google Play -kaupassa, noudata seuraavaa hyväksi havaittua ammattimaista työnkulkua:

1.  **Versionumeron kasvattaminen (`pubspec.yaml`):**
    *   Etsi kohta `version: 1.0.0+1`.
    *   `+` -merkin edellä on käyttäjille näkyvä julkaisuversio (esim. `1.0.1`). Kasvata sitä päivityksen koon tai uusien ominaisuuksien mukaan (Major.Minor.Patch).
    *   **Build Number:** Sanan `+` jälkeistä numeroa (esim. `+2`) **pitää aina kasvattaa yhdellä**. Play Kauppa hylkää paketin suoraan, jos sama Build Number on jo kertaalleen ladattu palveluun aikaisemmin.
2.  **Käännä uusi App Bundle:**
    *   Aja komento: `flutter build appbundle --release`
    *   Tämä luo uuden ladataan valmiin `.aab` -tiedoston.
3.  **Sisäinen testaus (Internal / Closed Testing):**
    *   Lataa uusi `.aab` aina ensin Play Consolen "Internal Testing" tai "Closed Testing" -kanavalle.
    *   Testaa omalla tiimillä tai valituilla käyttäjillä, ettei uusi ominaisuus tai build-prosessi riko mitään oikeissa puhelimissa tuotantoympäristössä.
4.  **Vaiheittainen julkaisu (Staged Rollout):**
    *   Kun tuot päivityksen Tuotanto (Production) -kanavalle, julkaise se portaittain (esim. ensin 10% käyttäjistä -> myöhemmin 50% -> lopulta 100%).
    *   Tällöin jos uusi versio sattuu sisältämään kriittisen kaatuman (crash), julkaisun voi keskeyttää ennen kuin se osuu kaikkiin käyttäjiin.
5.  **Julkaisutiedotteet (Release Notes):**
    *   Kirjaa ylös `CHANGELOG.md` -tiedostoon tms., mitä uutta versio sisältää. Nämä tekstit on helppo kopioida suoraan Play Kaupan päivityskuvaukseen.

### 5.2 Suora jakelu ilman Play Kauppaa (Sideloading .apk)

Mobiilisovellus voidaan jakaa käyttäjille myös täysin ilman Google Play -kaupan valvontaa suorana latauslinkkinä:

1.  **Käännä APK:** Aja sovelluksen juuressa `flutter build apk --release`. Tämä luo itsenäisen `app-release.apk` -tiedoston (koko n. 20-30 MB).
2.  **Houstaus:** Lataa `.apk` esimerkiksi suoraan Cloudflare Pages -sivustollesi (`frontend/public/` -kansioon) tai GitHub Releases -sivulle.
3.  **Lataaminen:** Lisää projektisi nettisivulle nappi "Lataa Androidille (.apk)". Linkitä se suoraan hostaamaasi `.apk` -tiedostoon (esim. `https://sun-domaini.com/personal-ai-coach.apk`).
4.  **Asennus Laitteessa:** Kun käyttäjä lataa tiedoston puhelimellaan ja yrittää avata sen, Android varoittaa oletuksena tuntemattomasta lähteestä. Käyttäjän tulee ohjeiden mukaisesti sallia Androidin tila-asetuksista "Salli asennus tästä lähteestä" (Chrome / puhelimen selain), jonka jälkeen asennus onnistuu paikallisesti täydellisesti.
