# Backend & Frontend Testaus – Yleiskatsaus

**Päivitetty:** 2026-02-09  
**Tila:** Testit Toteutettu & Dokumentoitu

---

## Yhteenveto

Health AI sisältää kattavan testikattavuuden, johon kuuluvat **yksikkötestit** (nopeat, mockatut), **integraatiotestit** (oikeat Firebase-toiminnot) sekä **End-to-End (E2E) testit** (käyttöliittymä).

### Testikattavuus

| Testityyppi | Määrä | Tila | Suoritusaika | Riippuvuudet |
|-------------|-------|------|--------------|--------------|
| Unit Tests | 20 | Valmis | ~2s | Ei (mockattu) |
| Integration Tests | 8 | Valmis | ~5s | Firebase |
| E2E Tests | 6 | Valmis | ~15s | Selain + Backend |

---

## Backend-testit (pytest)

### Testien ajaminen

```bash
# Kaikki testit
cd backend
python -m pytest tests/ -v

# Pelkät yksikkötestit (nopeat, eivät vaadi Firebasea)
python -m pytest tests/unit/ -v

# Pelkät integraatiotestit (vaativat service_account_key.json)
python -m pytest tests/integration/ -v

# Yksittäinen testitiedosto
python -m pytest tests/unit/test_ai_coaching.py -v
```

### Testien rakenne

```
backend/tests/
├── conftest.py              # Jaetut fixturet
├── unit/                    # Yksikkötestit (mockatut)
│   ├── test_ai_coaching.py  # AI-valmennus logiikka
│   ├── test_coaching_routes.py  # API route testit
│   ├── test_feedback.py     # Feeddback-endpointin testit
│   └── test_goals.py        # Tavoite-endpointin testit
└── integration/             # Integraatiotestit (oikea Firebase)
    └── test_firestore.py    # Firestore CRUD -operaatiot
```

### Unit Test -esimerkkejä

```python
# test_ai_coaching.py
def test_readiness_calculation():
    """Testaa vireystilan laskenta mockatulla datalla."""
    mock_data = {"body_battery": 80, "sleep_score": 85}
    result = calculate_readiness(mock_data)
    assert result > 0

def test_insight_caching():
    """Testaa että oivallukset cachetetaan 24h."""
    # Ensimmäinen kutsu -> luodaan oivallus
    # Toinen kutsu -> palautetaan cache
```

### Integration Test -esimerkkejä

```python
# test_firestore.py  
def test_create_and_delete_goal(real_firebase):
    """CRUD-operaatio oikeaa Firestorea vasten."""
    goal = {"activity_type": "Running", "target_value": 30}
    goal_id = db.create_goal(test_uid, goal)
    assert goal_id is not None
    
    # Cleanup
    db.delete_goal(test_uid, goal_id)
```

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

### E2E Test -esimerkkejä

```typescript
// login_page.spec.ts
test('should display login page correctly', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByText('Sign in with Google')).toBeVisible();
  await expect(page.getByText('Sign in with Apple')).toBeVisible();
});

// dashboard.spec.ts
test('should redirect to login if not authenticated', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL('/login');
});
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

## Liittyvä dokumentaatio

- [API-dokumentaatio](API.md) – Testattavat endpointit
- [Autentikaatio](authentication.md) – Token-validoinnin testaus
- [Arkkitehtuuri](arkkitehtuuri.md) – Testattavat komponentit
