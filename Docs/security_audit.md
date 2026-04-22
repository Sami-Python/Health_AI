# Tietoturva & Multi-User Auditointi

**Päivämäärä:** 22.4.2026 (Päivitetty, alkuperäinen 29.1.2026)  
**Projekti:** Health AI Coach  
**Tila:** TUOTANNOSSA (Multi-User, Production Ready)

---

## Tiivistelmä (Executive Summary)

Sovellus on auditoitu ja todettu **tietoturvalliseksi usean käyttäjän ympäristössä**. Kaikki kriittiset toiminnot vaativat kirjautumisen, ja jokaisen käyttäjän data on eristetty tiukasti toisistaan. Salasanat salataan AES-256-algoritmilla ja admin-endpointit vaativat erillisen roolin.

**Yleisarvosana:** **A** (Tuotantovalmis)

---

## 1. Kirjautuminen & Tunnistautuminen

| Tarkistuskohde | Tila |
|---|---|
| Firebase Auth integraatio (Google Sign-In) | ✅ OK |
| JWT Token Verification (kaikki endpointit) | ✅ OK |
| Token expiry (1h + auto-refresh) | ✅ OK |
| Logout (kutsuu `auth.signOut()`) | ✅ OK |
| Apple Sign-In (konfiguraatio) | ✅ OK |

---

## 2. Datan Eristys (Multi-User Isolation)

| Tarkistuskohde | Tila |
|---|---|
| Goals: Subcollection `users/{uid}/goals` | ✅ OK |
| Workouts: Subcollection `users/{uid}/workouts` | ✅ OK |
| Profile: `users/{uid}/profile` | ✅ OK |
| Insights: `users/{uid}/daily_insights` (24h cache) | ✅ OK |
| Garmin Credentials: `users/{uid}/garmin_credentials` (AES-256) | ✅ OK |
| Weekly Summaries: `users/{uid}/weekly_summaries` | ✅ OK |
| Garmin Metrics: `users/{uid}/garmin_daily_metrics` | ✅ OK |

**Kriittinen huomio:** Kaikki Firestore-kyselyt käyttävät `user_id`-suodatinta tai käyttäjäkohtaista subkokoelmaa. Ei ole mahdollista hakea toisen käyttäjän dataa API:n kautta.

---

## 3. API Tietoturva

| Tarkistuskohde | Tila |
|---|---|
| Rate Limiting (slowapi, endpoint-kohtaiset rajoitukset) | ✅ OK |
| CORS rajattu ympäristökohtaisesti (dev: localhost, prod: personalaicoach.ai) | ✅ OK |
| Ei SQL Injection riskiä (Firestore NoSQL) | ✅ OK |
| Garmin-salasanan salaus (AES-256 Fernet, `cryptography`-kirjasto) | ✅ OK |
| Garmin-tokenien salaus (AES-256, tallennettu Firestoreen) | ✅ OK |
| Security event -lokitus (Firestore `security_events`-kokoelma) | ✅ OK |

---

## 4. Admin & Infrastruktuuri

| Tarkistuskohde | Tila |
|---|---|
| Admin Role separation (`verify_admin` middleware, ADMIN_EMAILS env) | ✅ Toteutettu |
| Request audit logging (strukturoitu JSON-loggaus, Cloud Logging) | ✅ Toteutettu |
| Rate limit -loukkausten kirjaus Firestoreen | ✅ Toteutettu |
| Google Cloud Error Reporting (tuotanto) | ✅ Toteutettu |
| Prometheus-monitorointi | ✅ Toteutettu |
| Encryption Key hallinta (Secret Manager / env var) | ✅ Toteutettu |
| Service Account Key poistettu Git-historiasta (filter-repo) | ✅ Korjattu 22.4.2026 |

---

## 5. GDPR-yhteensopivuus

| Tarkistuskohde | Tila |
|---|---|
| Käyttäjän datan lataus (`GET /user/export`) | ✅ OK |
| Tilin ja datan poisto (`DELETE /account`) | ✅ OK |
| Batch delete kaikista subkokoelmista | ✅ OK |
| Salasana salattu (ei plain text Firestoressa) | ✅ OK |

---

## 6. Kehityskohteet

| Prioriteetti | Kohde | Tila |
|---|---|---|
| Matala | IP whitelisting admin-endpointeille | Harkinnassa |
| Matala | Firestore Security Rules fine-tuning | Harkinnassa |
| Matala | Pre-commit hooks (ruff, secret scanning) | Harkinnassa |

---

## 7. Johtopäätös

Sovellus täyttää tuotannon tietoturvavaatimukset usean käyttäjän ympäristössä. Kaikki data on eristetty käyttäjäkohtaisesti, arkaluonteinen data salattu, ja admin-toiminnot vaativat erillisen roolin. Tietoturvaloukkausten seuranta on toteutettu Firestoreen ja Cloud Reportingiin. **Arvosana nostettu A-:sta A:han** alkuperäisten puutteiden (admin-roolit, audit logging) korjausten myötä.
