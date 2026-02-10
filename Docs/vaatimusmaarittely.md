# Vaatimusmäärittely – Health AI Coach

**Versio:** 1.0  
**Status:** Production Ready  
**API:** v1.0.0

---

## Projektin Kuvaus

Dataohjautuva valmennusjärjestelmä, joka yhdistää:
- **Garmin-data** (Body Battery, uni, stressi, treenit)
- **XGBoost ML-malli** (vireystilan ennustus)
- **Google Gemini AI** (personoidut treenisuositukset)

**Tech Stack:**
- Frontend: Next.js 14 + TypeScript + Tailwind
- Backend: Python 3.12 + FastAPI
- Database: Firebase Firestore
- AI: Google Gemini 2.5 Flash
- ML: XGBoost + MLflow

---

## 1. Käyttäjähallinta

### 1.1 Rekisteröityminen ja Kirjautuminen

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-U1 | Google Sign-In (Firebase Auth) | Valmis |
| REQ-U2 | Apple Sign-In | Valmis (konfiguraatio odottaa) |
| REQ-U3 | Protected Routes (Suojatut sivut) | Valmis |
| REQ-U4 | Token-pohjainen API-autentikointi | Valmis |

### 1.2 Käyttäjäprofiili

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-P1 | Profiilin tallennus (ikä, paino, pituus) | Valmis |
| REQ-P2 | Garmin-tunnusten syöttö UI:lla | Valmis |
| REQ-P3 | Garmin-salasanan salaus (AES-256) | Valmis |
| REQ-P4 | GDPR: Oman datan lataus | Valmis |
| REQ-P5 | GDPR: Tilin ja datan poisto | Valmis |

---

## 2. Dashboard

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-D1 | Päivittäinen AI-oivallus (Readiness Insight) | Valmis |
| REQ-D2 | Metriikat: Body Battery, Uni, Stressi, HRV | Valmis |
| REQ-D3 | Treenihistoria (viimeiset 30 päivää) | Valmis |
| REQ-D4 | Aktiiviset tavoitteet edistymispalkeilla | Valmis |
| REQ-D5 | Seuraava suositeltu treeni | Valmis |

---

## 3. AI-valmennus

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-A1 | XGBoost-malli: Vireystilan ennustaminen | Valmis |
| REQ-A2 | Gemini AI: Luonnollinen valmentajateksti | Valmis |
| REQ-A3 | Oivalluksen välimuistitus (24h per käyttäjä) | Valmis |
| REQ-A4 | AI Chat: Kontekstuaalinen keskustelu | Valmis |
| REQ-A5 | Guardrails: Vain terveys/fitness aihealue | Valmis |

---

## 4. Tavoitteiden hallinta

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-G1 | Tavoitteen luominen (aktiviteetti, tavoite, jakso) | Valmis |
| REQ-G2 | Tavoitteen muokkaus ja poisto | Valmis |
| REQ-G3 | Automaattinen edistymislaskenta | Valmis |
| REQ-G4 | Visuaalinen edistymispalkki | Valmis |

---

## 5. Garmin-integraatio

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-I1 | Garmin-datan haku (garminconnect-kirjasto) | Valmis |
| REQ-I2 | Tietojen päivitys pyynnöstä (Refresh) | Valmis |
| REQ-I3 | Dashboard-banneri jos Garmin ei yhdistetty | Valmis |

---

## 6. Tietoturva

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-S1 | Firebase Token Verification (kaikki endpointit) | Valmis |
| REQ-S2 | Rate Limiting (slowapi) | Valmis |
| REQ-S3 | CORS-rajaukset ympäristökohtaisesti | Valmis |
| REQ-S4 | Garmin-salasanan AES-256 salaus | Valmis |
| REQ-S5 | Admin-endpointit eristetty | Valmis |
| REQ-S6 | Row-level Security (user_id-filtteröinti) | Valmis |

---

## 7. Käyttöliittymä

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-F1 | Responsiivinen (Mobile + Desktop) | Valmis |
| REQ-F2 | Dark Mode -teema | Valmis |
| REQ-F3 | Loading-tilat (Skeletonit) | Valmis |
| REQ-F4 | Toast-ilmoitukset (virheet & onnistumiset) | Valmis |
| REQ-F5 | Interaktiivinen AI Chat -sivu | Valmis |

---

## 8. DevOps & Infrastruktuuri

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-X1 | Docker-konttien käyttö | Valmis |
| REQ-X2 | GitHub Actions CI/CD (Cloud Run) | Valmis |
| REQ-X3 | MLflow eksperimenttien seuranta | Valmis |
| REQ-X4 | Prometheus + Grafana (monitorointi) | Valmis |
| REQ-X5 | Google Cloud Error Reporting | Valmis |
| REQ-X6 | MkDocs-dokumentaatiosivusto | Valmis |

---

## 9. Testaus

| Vaatimus | Kuvaus | Tila |
|----------|--------|------|
| REQ-T1 | Backend Unit Tests (pytest, mockattu) | Valmis |
| REQ-T2 | Backend Integration Tests (FirestoreManager) | Valmis |
| REQ-T3 | Frontend E2E Tests (Playwright) | Valmis |

---

## API-endpointit (Yhteenveto)

| Endpoint | Metodi | Kuvaus | Rate Limit |
|----------|--------|--------|------------|
| `/health` | GET | Terveystarkistus | – |
| `/goals` | GET/POST/PUT/DELETE | Tavoitteet | 20/min |
| `/workouts/next` | GET | Seuraava treeni | 20/min |
| `/workouts/history` | GET | Treenihistoria | 20/min |
| `/workouts/log` | POST | Manuaalinen kirjaus | 20/min |
| `/ai/insight` | GET | AI-oivallus | 10/min |
| `/ai/generate-plan` | POST | AI-treeniohjelma | 5/h |
| `/user/profile` | GET/POST | Käyttäjäprofiili | 20/min |
| `/user/export` | GET | GDPR: Data export | 3/h |
| `/user/account` | DELETE | GDPR: Tilin poisto | 1/h |
| `/garmin/credentials` | POST | Garmin-yhteys | 5/h |
| `/garmin/status` | GET | Garmin-tila | 20/min |
| `/system/refresh` | POST | Data refresh | 2/h |
| `/feedback` | POST | Palaute | 10/h |
| `/admin/feedback` | GET | Admin palautteet | 20/min |
| `/admin/security-events` | GET | Admin tietoturva | 50/min |
| `/admin/revoke-tokens/{uid}` | POST | Admin uloskirjaus | 5/min |

---

## Hyväksyntäkriteerit

Projekti täyttää kaikki vaatimukset, kun:

1. Käyttäjä voi kirjautua sisään Google-tilillä
2. Dashboard näyttää Garmin-metriikat ja AI-oivalluksen
3. Käyttäjä voi luoda, muokata ja poistaa tavoitteita
4. AI Chat vastaa vain terveys/fitness-kysymyksiin
5. Jokaisen käyttäjän data on eristetty (multi-user)
6. API on suojattu (token + rate limiting)
7. GDPR: Käyttäjä voi ladata datansa ja poistaa tilinsä
8. Testit menevät läpi (unit + integration + E2E)
9. Docker-ympäristö toimii yhdellä komennolla

---

**Viimeksi päivitetty:** 2026-02-09
