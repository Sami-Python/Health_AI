# 🧪 E2E Testaus (Playwright)

Tämä dokumentti kuvaa Health AI Coach -projektin **End-to-End (E2E)** testauksen, joka on toteutettu [Playwrightilla](https://playwright.dev/).

## 🛠️ Esivaatimukset

Testien ajaminen vaatii, että sinulla on asennettuna:
- **Node.js** (v18+)
- **NPM**

Testit sijaitsevat kansiossa `frontend/e2e/`. Konfiguraatio on tiedostossa `frontend/playwright.config.ts`.

## 🚀 Testien Ajaminen

Koska Next.js:n `dev`-palvelin (Turbopack) kanssa on havaittu yhteensopivuusongelmia testiajossa, testit ajetaan tällä hetkellä **tuotantobuildia** vasten.

1.  **Mene frontend-kansioon:**
    ```bash
    cd frontend
    ```

2.  **Rakenna sovellus (Build):**
    ```bash
    npm run build
    ```

3.  **Käynnistä sovellus (Start):**
    ```bash
    npm run start
    ```
    *(Varmista että sovellus on käynnissä osoitteessa `http://localhost:3000`)*

4.  **Aja testit:**
    Avaa uusi terminaali ja komenna:
    ```bash
    npx playwright test
    ```

### Testikomennot

| Komento | Kuvaus |
| :--- | :--- |
| `npx playwright test` | Ajaa kaikki testit (headless-tilassa). |
| `npx playwright test --ui` | Avaa interaktiivisen testikäyttöliittymän. |
| `npx playwright test --project=chromium` | Ajaa testit vain Chrome-selaimella. |
| `npx playwright show-report` | Näyttää viimeisimmän testiraportin (HTML). |

## 📋 Kattavuus

Tällä hetkellä E2E-testit kattavat seuraavat kriittiset polut:

### 1. Landing Page (`landing_page.spec.ts`)
- Varmistaa, että etusivu latautuu oikein.
- Tarkistaa, että pääotsikko ("Personal AI Coach") on näkyvissä.
- Varmistaa, että "Log In" (CTA) -painike on olemassa.

### 2. Login Page (`login_page.spec.ts`)
- Navigaatiotesti: Landing Page -> Login Page.
- Varmistaa, että kirjautumissivu renderöityy.
- Tarkistaa, että "Sign in with Google" -painike on käytettävissä.

## 🔧 Vianetsintä (Troubleshooting)

### Portti 3000 varattu
Jos saat virheen `Error: Address already in use`, se tarkoittaa että Next.js on jäänyt taustalle päälle.
1. Etsi prosessi: `netstat -ano | findstr :3000` (Windows)
2. Tapa prosessi: `taskkill /PID <PID> /F`

### Turbopack-virheet
Jos `npm run dev` (Turbopack) kaatuu Tailwind-virheisiin, käytä testaukseen aina **tuotantobuildia** (`npm run build && npm run start`), kuten yllä ohjeistettu. Tämä on kestävämpi tapa ajaa E2E-testejä CI-ympäristössä.

## 🤖 CI/CD Integraatio

Testit on suunniteltu ajettavaksi osana **GitHub Actions** CI-putkea. Jokainen Pull Request käy läpi automaattisen testauksen ennen mergeä, mikä estää rikkinäisten muutosten pääsyn tuotantoon. 
