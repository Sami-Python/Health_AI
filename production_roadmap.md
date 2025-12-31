# 🚀 Health AI: Production Scaling Roadmap (0 -> 10,000 Users)

Jos sovellus skaalattaisiin tuhansille käyttäjille, nykyinen "Local Single-User App" -arkkitehtuuri pitäisi muuttaa moderniksi pilviarkkitehtuuriksi.

## 1. Arkkitehtuuri & Backend (Cloud Native)
Nykyinen Streamlit + lokaali Python-skripti ei skaalaudu.
- [x] **Erota Frontend ja Backend:** Siirry pois monoliittisesta Streamlit-rakenteesta. (Aloitettu: Home View hakee datan API:sta)
- [x] **Backend-valinta:** Ota käyttöön FastAPI (Python) tai Node.js API:n rakentamiseen.
- [x] **API-suunnittelu:** Määrittele REST tai GraphQL rajapinta Fronendin käyttöön.
- [x] **Kontitus:** Paketoi sovellus Docker-konteiksi (Backend, Frontend).
- [ ] **Hosting:** Valmistele Kubernetes tai Cloud Run ympäristö.

## 2. Tietokanta (Multi-User & Scalability)
Nykyinen DuckDB/SQLite on tiedostopohjainen ja lukittuu usealla käyttäjällä.
- [-] **DB-migraatio:** Vaihda DuckDB -> PostgreSQL. (SKIP: Pysytään toistaiseksi DuckDB:ssä "Hybridimallilla")
- [ ] **Skaalautuvuus:** Salli satojen yhtäaikaisten yhteyksien käsittely (Connection pooling).
- [ ] **Time-Series Data:** Harkitse InfluxDB/TimescaleDB sensoridatalle jos tarpeen.
- [ ] **Data Isolation:** Implementoi Row-Level Security ja `user_id` jokaiseen tauluun.

## 3. Käyttäjähallinta & Tietoturva (Security)
- [ ] **Autentikaatio:** Ota käyttöön OAuth2 / OpenID Connect (Auth0, Firebase Auth).
- [ ] **Kirjautuminen:** Toteuta Google/Apple/Email -kirjautumisvaihtoehdot.
- [ ] **Tietosuoja (GDPR):** Varmista datan salaus (At-Rest & In-Transit).
- [ ] **Datan hallinta:** Työkalu käyttäjän datan poistoon ("Oikeus tulla unohdetuksi").

## 4. AI & Mallit (LLM at Scale)
Nykyinen suora Gemini API -kutsu voi hidastua tai maksaa liikaa.
- [ ] **Mallien optimointi:** Vaihda kevyempään malliin (esim. Gemini Flash) rutiinitehtävissä.
- [ ] **Välimuisti (Caching):** Implementoi vastausten välimuisti samanlaisille kyselyille.
- [ ] **Rate Limiting:** Rajoita API-kutsujen määrää per käyttäjä väärinkäytösten estämiseksi.

## 5. Frontend (Käyttökokemus)
Streamlit on raskas tuhansille yhtäaikaisille käyttäjille.
- [ ] **Moderni Web-kehys:** Rakenna käyttöliittymä Reactilla, Vuella tai Next.js:llä.
- [ ] **Mobiilisovellus:** Harkitse React Nativea tai Flutteria natiivia kokemusta varten.
- [ ] **Notifikaatiot:** Lisää Push-ilmoitukset (treenimuistutukset).
- [ ] **Integraatiot:** Kytke Apple Health / Google Fit -rajapintoihin.

## 6. DevOps & Monitoring
- [ ] **CI/CD Pipeline:** Laajenna GitHub Actions kattamaan automaattinen deploy (CD).
- [ ] **Monitorointi:** Asenna Grafana/Datadog suorituskyvyn seurantaan.
- [ ] **Alerting:** Määritä hälytykset virhetilanteista (esim. API vastaa hitaasti).

---
### MVP -> Beta (Ensimmäiset askeleet)
- [-] Konfiguroi PostgreSQL-tietokanta. (SKIP)
- [x] Luo uusi FastAPI-projekti Backuiksi.
- [ ] Integroi Firebase Auth.
