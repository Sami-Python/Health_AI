# Personal AI Coach – Dokumentaation aloitussivu

**Personal AI Coach** on älykäs, dataohjautuva valmennusjärjestelmä kestävyysurheilijoille. Se yhdistää fysiologisen datan automaattisen keräyksen, koneoppimispohjaisen palautumisennusteen ja generatiivisen tekoälyvalmentajan yhdeksi saumattomaksi kokonaisuudeksi.

🌐 **Julkinen sivu:** [www.personalaicoach.ai](https://www.personalaicoach.ai)  
📱 **Web-sovellus:** [app.personalaicoach.ai](https://app.personalaicoach.ai)  
🔌 **Backend API (Swagger):** [Cloud Run / Swagger UI](https://health-ai-backend-35976089058.europe-north1.run.app/docs)

---

## Mitä sovellus tekee?

### 1. Kerää fysiologinen data automaattisesti (Garmin)
Sovellus hakee päivittäin Garmin Connect -palvelusta:
- **Body Battery** – Garminin laskema palautumisindeksi (0–100)
- **Unimetriikka** – Unen kesto ja laatu (`totalSleep_minutes`, unilaatu)
- **Stressitaso** – Päivän keskilataus sympathisen hermoston aktivaatiosta
- **Harjoituskuorma** – GPS-treenit, teho/sykedatan aktiviteettihistoria
- **Askelmäärä & Aktiivisuus** – Kevyt päivittäinen liike

Data haetaan `fetch_garmin_data.py`-skriptillä joka tunnistettaessa, tallennetaan CSV-välimuistiin ja synkronoidaan Firestoreen.

### 2. Laskee harjoittelun fysiologiset metriikat (TSB/CTL/ATL)
`process_garmin_data.py` laskee klassisen urheilufysiologian kuormitusmittarit:

| Metriikka | Nimi | Kuvaus |
|-----------|------|--------|
| **CTL** | Chronic Training Load | 42 päivän eksponentiaalinen liukuva keskiarvo kuormituksesta → "Fitness" |
| **ATL** | Acute Training Load | 7 päivän liukuva keskiarvo → "Fatigue" |
| **TSB** | Training Stress Balance | `CTL – ATL` → "Form" (positiivinen = levännyt, negatiivinen = väsynyt) |

Nämä metriikat syötetään sekä ML-mallille opetusaineistoksi että käyttöliittymän graafeihin.

### 3. Ennustaa palautumistilan koneoppimisella (XGBoost)
**Tavoite:** Ennustaa seuraavan aamun `bodyBatteryHighestValue` (0–100) nykyisten fysiologisten signaalien perusteella – tarkemmin kuin Garminin oma laitekohtainen arvio.

**Malli:** XGBoost (Gradient Boosted Trees)
- **Opetusdatapipeline:** CSV-historia → feature engineering → `GridSearchCV`-hyperparametrioptimointia → ristiinvalidointi (`TimeSeriesSplit`) → malli tallennetaan `xgb_model.pkl`
- **Tärkeimmät piirteet** (feature importance -analyysin perusteella):
  1. `bodyBatteryHighestValue` (edellinen päivä) – vahvin ennustaja
  2. `bodyBatteryDuringSleep` – unen aikainen lataus
  3. `poor_night_flag` – binäärinen lippu, jos unilaatu < 45 pistettä
  4. `averageStressLevel` – tämän päivän stressi ennustaa huomisen tilaa
  5. `TSB` – harjoitusmuoto (Form)
- **Tarkkuus:** R² ≈ 0.67–0.83 riippuen datan pituudesta (vähintään 30 päivää tarvitaan)
- **Inkrementaalinen oppiminen:** Oletuksena malli päivitetään vain uudella datalla; `--mode full` tekee koko uudelleenkoulutuksen (GridSearchCV)

**MLOps:** Jokainen ajokerta kirjataan MLflow-kokeilurekisteriin (`sqlite:///backend/data/mlflow.db`) parametreineen, metriikoineen ja artefakteineen.

### 4. Tarjoaa henkilökohtaisen AI-valmentajan (Gemini 2.0 Flash)

Sovelluksessa on kaksi erillistä Gemini-integraatiota:

#### A) Proaktiivinen AI Coach (`ai_coach.py`)
- Kutsutaan `/ai/insight`- ja `/plans/generate`-endpointeissa
- Hakee käyttäjän tuoreimman fysiologisen tilanteen (Body Battery, TSB, ATL-kasvu, unitrendi, aktiiviset tavoitteet)
- Rakentaa kontekstuaalisen promptin, jossa se:
  - Tulkitsee Body Batteryn (0–39=kriittinen, 40–59=matala, 60–74=hyvä, 75–100=erinomainen)
  - Laskee loukkaantumisriskin (`ATL_growth` % vs `sleep_change` h/yö)
  - Ottaa huomioon käyttäjän tavoitteet (kilpailu, viikkokuorma)
- Generoi päivittäisen oivalluksen **ja** 3–7 päivän treeniohjelman askeleilla (Warmup → Interval → Recovery)
- Treenit voidaan viedä suoraan Garmin-kelloon (Send to Garmin)

#### B) Interaktiivinen Chat Coach (`ai_chat_manager.py`)
- Kutsutaan `/ai/chat`-endpointissa
- Ylläpitää sessiokohtaista keskusteluhistoriaa (max 10 viestiä kontekstina)
- Tiukat guardrailit: vastaa vain valmennusaiheisiin kysymyksiin
- Käyttää `Gemini Flash 2.5` -mallia nopeuden vuoksi
- Saatavilla sekä web- että mobiilisovelluksessa

**Päivittäinen välimuisti:** AI-oivallus lasketaan vain kerran päivässä per käyttäjä Firestoreen (`users/{uid}/daily_insights/{date}`), jotta Google AI -kiintiöt eivät ylity.

---

## Järjestelmän osat

| Komponentti | Teknologia | Kuvaus |
|-------------|-----------|--------|
| **Landing Page** | HTML/CSS → Cloudflare Pages | Julkinen markkinointisivu |
| **Web-sovellus** | Next.js + TypeScript | Selainpohjainen dashboard |
| **Mobiilisovellus** | Flutter 3.41.2 | Android & iOS natiivi |
| **Backend API** | Python 3.12 + FastAPI v1.0.0 | REST API, Cloud Run |
| **Tietokanta** | Firebase Firestore | Käyttäjädata, NoSQL |
| **Auth** | Firebase Authentication | JWT Bearer Token |
| **ML-malli** | XGBoost + scikit-learn | Palautumisennuste |
| **AI-valmennus** | Google Gemini 2.0 Flash | LLM-pohjainen coach |
| **Garmin Auth** | curl_cffi + Android SSO | Universal Fix v4 |
| **Seuranta** | MLflow (SQLite) | Koehistoria & versiot |
| **Monitorointi** | Prometheus + Grafana + Cloud Logging | Observability |

---

## Dokumentaatiolinkit

| Sivu | Kuvaus |
|------|--------|
| [Arkkitehtuuri](arkkitehtuuri.md) | Järjestelmäkaavio, komponentit, datavirrat |
| [API-viite](API.md) | Kaikki REST-endpointit, esimerkit, rate limitit |
| [Garmin-asennus](garmin_setup.md) | Tunnusten liittäminen, Universal Fix v4 |
| [Garmin Bypass](garmin_cloudflare_bypass_v4.md) | Android SSO -ratkaisun post-mortem |
| [Autentikaatio](authentication.md) | Firebase Auth, token flow, data isolation |
| [Testaus](testing.md) | pytest, Playwright E2E, CI/CD |
| [Havainnoitavuus](observability.md) | Prometheus, Grafana, Cloud Logging |
| [Tietoturva-auditointi](security_audit.md) | Tietoturvahavainnot ja tila (A-) |
| [Julkaisu](deployment.md) | Cloud Run, Cloudflare Pages, CI/CD |
| [MLflow](MLflow.md) | ML-kokeiden seuranta ja mallirepo |
| [Roadmap V2](roadmap_v2.md) | Tulevat ominaisuudet (Proactive AI, App Store) |
| [Kehityspäiväkirja](sami_memo.md) | Yksityiskohtainen muutoshistoria session kerrallaan |

---

## Pikakäynnistys

```bash
# 1. Backend (portti 8000)
cd backend
.venv\Scripts\Activate.ps1          # Windows PowerShell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 2. Web-frontend (portti 3000)
cd frontend && npm run dev

# 3. Mobiili (Flutter, fyysinen Android-laite suositeltu)
cd mobile && flutter run

# 4. Testit
cd backend && python -m pytest tests/ -v

# 5. MLflow UI
cd backend && mlflow ui --backend-store-uri sqlite:///data/mlflow.db
```

---

## Nykytila (2026-04-18)

| Alue | Tila |
|------|------|
| Backend API | 🟢 Production (Cloud Run europe-north1) |
| Web Dashboard | 🟢 Live (app.personalaicoach.ai) |
| Mobiilisovellus (Android) | 🟢 Tuotantovalmis, APK jaossa |
| Garmin-synkronointi | 🟢 Stable (Universal Fix v4) |
| ML-malli (XGBoost) | 🟢 R² ≈ 0.67 (kasvaa datan karttuessa) |
| AI Coach (Gemini) | 🟢 Live, päivittäinen välimuisti |
| GDPR-yhteensopivuus | 🟢 Data export + tilin poisto |
| iOS-sovellus | ⏳ Suunniteltu (roadmap) |
