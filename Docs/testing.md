# Backend & Frontend Testaus - Yleiskatsaus

**Päivitetty:** 2026-02-09  
**Tila:** ✅ Testit Toteutettu & Dokumentoitu

---

## Yhteenveto

Health AI sisältää kattavan testikattavuuden, johon kuuluvat **yksikkötestit** (nopeat, mockatut), **integraatiotestit** (oikeat Firebase-toiminnot) sekä **End-to-End (E2E) testit** (käyttöliittymä).

### Testikattavuus

| Testityyppi | Määrä | Tila | Suoritusaika | Riippuvuudet |
|-------------|-------|------|--------------|--------------|
| **Yksikkötestit (Unit)** | 11 | ✅ Toteutettu | ~2-3s | Ei riippuvuuksia (mockattu) |
| **Integraatiotestit** | 20+ | ✅ Toteutettu | ~30-60s | Firebase Emulaattori tai testiprojekti |
| **Frontend E2E** | 4 | ✅ Toteutettu | ~10-20s | Playwright & Selaimet |

---

## Yksikkötestit (Backend)

**Tiedostot:**
- `backend/tests/test_endpoints.py` - API-päätepisteiden testit (8 testiä)
- `backend/tests/test_admin.py` - Admin-oikeuksien testit (3 testiä)
- `backend/tests/test_config.py` - Konfiguraatiotestit

**Mitä testataan:**
- ✅ Tavoitteiden luonti ja validointi
- ✅ Harjoitusmerkinnät (API)
- ✅ Admin-autentikaatio
- ✅ Tietokantavirheiden käsittely
- ✅ Virheilmoitukset

**Suoritusohje:**
```bash
cd backend
python -m pytest tests/test_endpoints.py tests/test_admin.py tests/test_config.py -v
```

---

## Integraatiotestit (Backend)

**Tiedostot:**
- `backend/tests/test_integration.py` - Pääintegraatiotestit (20+ testiä)
- `backend/tests/conftest_integration.py` - Firebase Emulaattori -fikstuurit
- `backend/tests/test_helpers.py` - Testiapurit

**Mitä testataan:**
- ✅ **Autentikaatio:** Tokenien validointi, käyttäjien eristys, admin-oikeudet
- ✅ **GDPR:** Tietojen vienti ja poisto (Firestore + Auth)
- ✅ **Garmin Integraatio:** AES-256 salaus/purku, tunnusten tallennus
- ✅ **Tietokanta:** CRUD-operaatiot (Goal, Workout, Profile)
- ✅ **Virhekäsittely:** Virheelliset syötteet, puuttuvat resurssit

**Suoritusohje (Emulaattorilla):**
```bash
# Terminaali 1: Käynnistä emulaattori
firebase emulators:start --only auth,firestore

# Terminaali 2: Aja testit
cd backend
python -m pytest tests/test_integration.py -v
```

---

## Frontend E2E Testit (Playwright)

**Tiedostot:**
- `frontend/e2e/landing_page.spec.ts` - Aloitussivun testit
- `frontend/e2e/login_page.spec.ts` - Kirjautumisen testit (Google Login Mock)
- `frontend/e2e/dashboard.spec.ts` - Hallintapaneelin testit (API Mock)

**Mitä testataan:**
- ✅ Aloitussivun renderöinti ja navigointi
- ✅ Kirjautumissivu ja "Sign in with Google" -painike
- ✅ **Google Login (Mock):** Simuloi onnistuneen Google-kirjautumisen ilman oikeaa tiliä (`_TEST_MODE_AUTH`)
- ✅ Hallintapaneelin (Dashboard) latautuminen ja komponentit (Navigaatio, Widgetit)

**Suoritusohje:**

1. **Asenna selaimet (ensimmäisellä kerralla):**
   ```bash
   cd frontend
   npx playwright install chromium
   ```

2. **Aja kaikki testit:**
   ```bash
   cd frontend
   npx playwright test
   ```

3. **Debuggaus (Visuaalinen käyttöliittymä):**
   ```bash
   npx playwright test --ui
   ```

**Huomio:** E2E-testit käyttävät erityistä "Test Mode" -tilaa (`AuthContext.tsx`), joka ohittaa oikean Firebase-kirjautumisen testauksen ajaksi. Tämä nopeuttaa testejä ja tekee niistä luotettavampia.

---

## Asennusohjeet

### Esivaatimukset

**Yksikkötestit:**
```bash
cd backend
pip install pytest pytest-asyncio
```

**Integraatiotestit (Emulaattori):**
Vaatii Javan asennuksen (`choco install openjdk11`) ja `firebase-tools` (`npm install -g firebase-tools`).

---

## Tuotantovalmius

**Status:**
- ✅ **Testit Toteutettu:** Kaikki kriittiset osat (Backend & Frontend) on testattu.
- ✅ **Dokumentaatio:** Ajantasalla (Suomeksi).
- 🟢 **Valmis Beta-vaiheeseen:** Kriittiset toiminnot varmistettu automaattitestein.

**Suositus:**
Aja `npx playwright test` ennen jokaista tuotantopäivitystä (`deploy`).
