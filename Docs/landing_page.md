# Aloitussivu (Landing Page) – Personal AI Coach

## Yleiskatsaus

Aloitussivu on Personal AI Coach -palvelun julkinen verkkosivusto, jota isännöidään **Cloudflare Pages** -alustalla. Se toimii pääasiallisena markkinointi- ja tietolähteenä uusille käyttäjille.

**Julkinen osoite:** https://www.personalaicoach.ai

---

## Ominaisuudet

### 1. Hero-osio
- Selkeä arvolupaus: "Your Personal AI Fitness Coach"
- Kaksi toimintokutsua (CTA): "Get Started" ja "See Demo"
- Moderni tumma teema liukuväri-efekteillä

### 2. Ominaisuuksien esittely
Kuusi korttia, jotka korostavat ydinominaisuuksia:
- **Älykäs Dashboard** – Reaaliaikaiset terveysmittarit
- **Harjoituskalenteri** – Tekoälyn suunnittelemat treenit
- **AI Valmentaja** – Henkilökohtaiset suositukset
- **Tavoitteiden seuranta** – Edistymisen monitorointi
- **Edistynyt analytiikka** – Suorituskyvyn oivallukset
- **Garmin-integraatio** – Automaattinen tietojen synkronointi

### 3. Visuaaliset demonstraatiot
- EKG-sykkeen visualisointi
- AI-analytiikan aivovisualisointi
- Puhelin-mockup sovelluksen esikatselulla

### 4. Miten se toimii
Kolmivaiheinen prosessi:
1. Yhdistä Garmin-laite
2. Saa tekoälyn tuottamia oivalluksia
3. Saavuta kuntotavoitteet

### 5. Latausosio
- **Android APK Lataus:** Suora `personal-ai-coach.apk` -latauslinkki (Sideloading) ilman sovelluskauppaa.
- App Store -merkki (iOS Tulossa pian)
- Mobiili edellä -suunnittelu

### 6. Odotuslista-widget (Waitlist)
- Ilmestyy automaattisesti 2 sekunnin kuluttua sivun latauksesta
- Sähköpostien keräys Firebase Firestore -integraatiolla
- Moderni glassmorphism-design tummalla teemalla
- Lomakkeen validointi ja onnistumis-/virheviestit
- LocalStorage-tallennus (ei näytetä uudelleen sulkemisen jälkeen)
- Analytiikan seuranta (`waitlist_popup_view`, `waitlist_signup`)
- Useita sulkemistapoja (X-painike, taustan klikkaus, automaattinen sulkeutuminen)

### 7. GDPR-yhteensopivuus (2026-02-06)
- **Tietosuojaseloste** (`privacy.html`) – Täysin GDPR-yhteensopiva tietosuojakäytäntö
- **Käyttöehdot** (`terms.html`) – Oikeudelliset ehdot
- **Evästebanneri (Cookie Consent)** – Hyväksy/Hylkää -painikkeet LocalStorage-tallennuksella
- **Ehdollinen analytiikka** – Firebase Analytics latautuu vain suostumuksen jälkeen
- Footer-linkit päivitetty osoittamaan lakisivuille

---

## Tekninen Stack

### Isännöinti (Hosting)
- **Alusta:** Cloudflare Pages
- **CDN:** Globaali reunaverkko (200+ sijaintia)
- **SSL/TLS:** Full (strict) -tila automaattisella HTTPS:llä
- **Oma verkkotunnus:** `www.personalaicoach.ai` + apex domain

### Frontend
- **HTML5** – Semanttinen merkkaus
- **CSS3** – Moderni tyylittely glassmorphism-efekteillä
- **JavaScript** – Vanilla JS interaktioita varten
- **Kuvat:** WebP-formaatti lazy loading -ominaisuudella

### Analytiikka
- **Firebase Analytics** – Sivun katselut, käyttäjäkäyttäytyminen (GDPR-yhteensopiva suostumuksella)
- **Tapahtumaseuranta:** CTA-klikkaukset, navigaatio
- **Firebase Firestore** – Odotuslistan sähköpostien keräys (`waitlist` kokoelma)
- **Evästehallinta:** Analytiikka latautuu vain jos evästeet hyväksytään

---

## Tiedostorakenne

```
landing_page/
├── index.html              # Pääsivu (HTML)
├── instructions.html       # Käyttöohjeet
├── privacy.html            # Tietosuojaseloste (GDPR)
├── terms.html              # Käyttöehdot
├── styles.css              # Tyylitiedosto
├── images/                 # Kuvat ja assetit
│   ├── hero_fitness.webp   # Hero-osion kuva
│   ├── ecg_visualization.webp
│   └── ai_analytics_brain.webp
├── firebase.json           # Firebase Hosting konfiguraatio (legacy)
├── .firebaseignore        # Firebase ignore -säännöt
├── README.md              # Käyttöopas
└── CLOUDFLARE_DEPLOYMENT.md  # Julkaisuohjeet
```

---

## Julkaisu (Deployment)

### Cloudflare Pages Konfiguraatio

**Projektiasetukset:**
- **Projektin nimi:** `personalaicoach-landing`
- **Tuotantohaara:** `main`
- **Kehysasetus:** None (staattinen sivu)
- **Build-komento:** (tyhjä)
- **Build-hakemisto:** `.`
- **Juurihakemisto:** `landing_page`

### Automaattiset julkaisut

Jokainen push `main`-haaraan käynnistää uuden julkaisun:

```bash
git add landing_page/
git commit -m "Päivitä aloitussivu"
git push origin main
```

Cloudflare Pages:
1. Tunnistaa push-tapahtuman
2. Rakentaa ja julkaisee (1-2 minuuttia)
3. Päivittää live-sivuston automaattisesti

### Manuaalinen julkaisu

Cloudflare Dashboardin kautta:
1. Mene Workers & Pages -osioon
2. Valitse `personalaicoach-landing`
3. Klikkaa "Create deployment"
4. Valitse haara ja julkaise

---

## Konfiguraatio

### DNS-tietueet (Automaattisesti konfiguroitu)

```
Type: CNAME
Name: www
Content: personalaicoach-landing.pages.dev
Proxy: Yes

Type: CNAME
Name: @
Content: personalaicoach-landing.pages.dev
Proxy: Yes
```

### SSL/TLS Asetukset

- **Salaustila:** Full (strict)
- **Always Use HTTPS:** Päällä
- **Automatic HTTPS Rewrites:** Päällä
- **SSL-sertifikaatti:** Aktiivinen ja automaattisesti uusiutuva

### Sähköpostin reititys

- **Sähköpostiosoite:** `info@personalaicoach.ai`
- **Uudelleenohjaus:** Konfiguroitu Cloudflare Email Routingin kautta
- **MX-tietueet:** Cloudflaren automaattisesti konfiguroimat

---

## Analytiikka & Seuranta

### Firebase Analytics Tapahtumat

Seuratut tapahtumat:
- `page_view` – Sivun lataukset
- `cta_click` – "Get Started" -painikkeen klikkaukset
- `demo_click` – "See Demo" -painikkeen klikkaukset
- `nav_click` – Navigaation interaktiot
- `waitlist_popup_view` – Odotuslista-popup näytetty
- `waitlist_signup` – Käyttäjä liittyi odotuslistalle (sisältää sähköpostin)

### Firestore Kokoelmat

**Odotuslista (Waitlist):**
- Kokoelma: `waitlist`
- Dokumentin kentät:
  - `email` (string) – Käyttäjän sähköposti
  - `timestamp` (timestamp) – Liittymisaika
  - `source` (string) – Aina "landing_page"
- Tietoturva: Julkinen kirjoitus (vain luonti), admin lukuoikeus

### Suorituskykymittarit

- **Globaali CDN:** Alle 100ms vasteajat maailmanlaajuisesti
- **HTTP/3:** Päällä nopeampia yhteyksiä varten
- **Brotli-pakkaus:** Optimoitu sisällön toimitus
- **Reuna-välimuisti (Edge Caching):** Salamannopeat sivulataukset

---

## Design-ohjeistus

### Väripaletti

```css
--primary: #6366f1 (Indigo)
--secondary: #8b5cf6 (Purple)
--accent: #06b6d4 (Cyan)
--background: #0f172a (Dark Blue)
--surface: rgba(255, 255, 255, 0.05) (Glassmorphism)
```

### Typografia

- **Otsikot:** System font stack (optimoitu suorituskyvylle)
- **Leipäteksti:** Sans-serif, 16px peruskoko
- **Responsiivisuus:** Skaalautuu mobiilista (14px) työpöytäversioon (18px)

### Efektit

- **Glassmorphism:** `backdrop-filter: blur(10px)`
- **Liukuvärit:** Lineaariset gradientit korteissa ja taustoissa
- **Animaatiot:** Pehmeät siirtymät (0.3s ease)
- **Hover-tilat:** Skaalaus- ja hehkuefektit

---

## Integraatio pääsovellukseen

### Linkit Frontend-sovellukseen

Kaikki "Get Started" ja "Login" -painikkeet ohjaavat osoitteeseen:
```
https://app.personalaicoach.ai
```

### API-dokumentaation linkki

Footerin linkki backend API-dokumentaatioon:
```
https://health-ai-backend-35976089058.europe-north1.run.app/docs
```

---

## Sisällön päivitys

### Tekstin päivitys

Muokkaa tiedostoa `landing_page/index.html`:

```html
<h1>Your Personal AI Fitness Coach</h1>
<p>Transform your training with AI-powered insights...</p>
```

### Kuvien päivitys

1. Lisää uusi kuva hakemistoon `landing_page/images/`
2. Muunna WebP-muotoon (suositeltavaa)
3. Päivitä HTML `<img>` -tagi:

```html
<img src="images/uusi_kuva.webp" alt="Kuvaus" loading="lazy">
```

### SEO Metadata

Päivitä `<head>` -osio tiedostossa `index.html`:

```html
<title>Personal AI Coach - AI-Powered Fitness Training</title>
<meta name="description" content="...">
<meta property="og:title" content="...">
```

---

## Vianmääritys

### Julkaisuongelmat

**Ongelma:** Muutokset eivät näy pushin jälkeen
**Ratkaisu:**
1. Tarkista Cloudflare Pages deployment -loki
2. Tyhjennä selaimen välimuisti (Ctrl+Shift+R)
3. Odota 2-3 minuuttia CDN:n päivittymistä

**Ongelma:** SSL-sertifikaattivirhe
**Ratkaisu:**
1. Varmista että SSL/TLS-tila on "Full (strict)"
2. Tarkista että oma verkkotunnus on aktiivinen Cloudflare Pagesissa
3. Odota enintään 24 tuntia sertifikaatin provisiointia

### Sähköpostiongelmat

**Ongelma:** Sähköpostin edelleenlähetys ei toimi
**Ratkaisu:**
1. Tarkista MX-tietueet Cloudflare DNS:ssä
2. Tarkista että kohdesähköposti on vahvistettu
3. Testaa lähettämällä viesti osoitteeseen `info@personalaicoach.ai`

---

## Liittyvä dokumentaatio

- [CLOUDFLARE_DEPLOYMENT.md](file:///c:/Users/samih/code/health_ai/landing_page/CLOUDFLARE_DEPLOYMENT.md) – Yksityiskohtainen julkaisuopas
- [README.md](file:///c:/Users/samih/code/health_ai/landing_page/README.md) – Aloitussivun yleiskatsaus
- [arkkitehtuuri.md](file:///c:/Users/samih/code/health_ai/Docs/arkkitehtuuri.md) – Järjestelmäarkkitehtuuri

---

## Tulevat parannukset

### Suunnitellut ominaisuudet
- [ ] Blogi-osio treenivinkeille
- [ ] Asiakaskertomusten karuselli (Testimonials)
- [ ] Sovelluksen ominaisuuksien videodemo
- [ ] Hinnastosivu (jos kaupallistetaan)
- [ ] FAQ-osio (Usein kysytyt kysymykset)
- [x] ~~Uutiskirjeen tilaus~~ → **Odotuslista-widget toteutettu** (2026-02-05)

### Suorituskyvyn optimointi
- [ ] HTML/CSS:n minifikointi
- [ ] Service Worker offline-tukea varten
- [ ] Preload-vihjeet kriittisille resursseille
- [ ] Kuvakokojen lisäoptimointi

### SEO-parannukset
- [ ] Strukturoitu data (JSON-LD)
- [ ] Sitemap.xml luonti
- [ ] Murupolku-navigaatio (Breadcrumbs)
- [ ] Lisää sisäisiä linkkejä

---

## Tuki

Aloitussivun ongelmatilanteissa:
- **Cloudflare Tuki:** https://cfl.re/3WgEyrH
- **Cloudflare Pages Dokumentaatio:** https://developers.cloudflare.com/pages/
- **Projektin Repository:** https://github.com/[your-repo]/health_ai

---

**Päivitetty:** 2026-02-06  
**Tila:** Tuotannossa  
**Julkaisualusta:** Cloudflare Pages  
**URL:** https://www.personalaicoach.ai
