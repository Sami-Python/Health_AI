# Backend & Frontend Testaus – Yleiskatsaus

**Päivitetty:** 2026-04-22  
**Tila:** Testit Toteutettu & Dokumentoitu

---

## Yhteenveto

Health AI sisältää kattavan testikattavuuden, johon kuuluvat **yksikkötestit** (nopeat, mockatut), **integraatiotestit** (oikeat Firebase-toiminnot) sekä **End-to-End (E2E) testit** (käyttöliittymä Playwright-selaintestinä).

### Testikattavuus

| Testityyppi | Tiedostoja | Tila | Suoritusaika | Riippuvuudet |
|-------------|-----------|------|--------------|--------------|
| Backend Unit | 6 | Valmis | ~3s | Ei (mockattu) |
| Backend Integration | 1 | Valmis | ~5s | Firebase |
| Frontend E2E | 2 | Valmis | ~15s | Selain + Backend |
| Mobile (Flutter) | – | Puuttuu | – | – |

---

## Backend-testit (pytest)

### Testien ajaminen

```bash
# Kaikki testit
cd backend
python -m pytest tests/ -v

# Pelkät yksikkötestit (nopeat, eivät vaadi Firebasea)
python -m pytest tests/ -v -k "not integration"

# Pelkät integraatiotestit (vaativat Firebase-yhteyttä)
python -m pytest tests/test_integration.py -v

# Yksittäinen testitiedosto
python -m pytest tests/test_endpoints.py -v
```

### Testien rakenne

```
backend/tests/
├── conftest.py                    # Jaetut fixturet (mockattu Firebase, test client)
├── conftest_integration.py        # Integraatio-fixturet
├── conftest_no_emulator.py        # Kiertotapa Javan puuttumiselle
├── test_admin.py                  # Admin-endpointit (verify_admin, security events)
├── test_config.py                 # Konfiguraation testit (Settings, env-luokitus)
├── test_endpoints.py              # API-endpointit (goals, workouts, profile)
├── test_garmin_2fa.py             # Garmin 2FA -login flow (MFA callback mock)
├── test_helpers.py                # Helper-funktiot (salaus, tokenit)
├── test_integration.py            # Firestore CRUD-integraatiotesti
├── test_workout_rescheduling.py   # AI-treenin uudelleenajoitus
├── verify_api_auth.py             # Auth-verifiointiskriipti (manuaalinen)
└── verify_firestore_isolation.py  # Multi-user eristyksen manuaalinen tarkistus
```

### Mitä testataan

| Tiedosto | Kattavuus |
|----------|-----------|
| `test_admin.py` | Admin middleware, security event logging |
| `test_config.py` | Settings factory, env-kohtaiset asetukset |
| `test_endpoints.py` | Goals CRUD, workout CRUD, profile, AI insight |
| `test_garmin_2fa.py` | Garmin login, MFA flow, token resume |
| `test_helpers.py` | AES-256 encrypt/decrypt, token generation |
| `test_workout_rescheduling.py` | Skip-and-reschedule AI logic |
| `test_integration.py` | Firestore CRUD (oikea yhteys) |

---

## Frontend E2E -testit (Playwright)

### Esivaatimukset

```bash
cd frontend
npm install
npx playwright install  # Lataa selaimet
```

### Testien ajaminen

```bash
# Kaikki E2E-testit
npx playwright test

# Yksittäinen testitiedosto
npx playwright test e2e/login_page.spec.ts

# UI-tilassa (näet selaimen)
npx playwright test --ui

# Debug-tilassa (step-by-step)
npx playwright test --debug
```

### Testien rakenne

```
frontend/e2e/
├── login_page.spec.ts      # Kirjautumissivun testit
└── dashboard.spec.ts       # Dashboardin testit
```

### Konfiguraatio

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:3000',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
  },
});
```

---

## CI/CD-integraatio

Backend-testit ajetaan automaattisesti GitHub Actions CI:ssä jokaisella push/PR:llä (`main`-haaraan):

```yaml
# .github/workflows/ci.yml
- name: Run Backend Tests
  run: python -m pytest tests/
```

> **Huom:** Playwright E2E -testejä ei ajeta CI:ssä tällä hetkellä. Flutter-testejä ei ole vielä toteutettu.

---

## Liittyvä dokumentaatio

- [Arkkitehtuuri](arkkitehtuuri.md) – Testattavat komponentit
- [Vaatimusmäärittely](vaatimusmaarittely.md) – Hyväksyntäkriteerit
