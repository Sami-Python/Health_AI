# 🚀 Quick Start
Tässä komennot projektin ajamiseen. Varmista, että olet oikeassa kansiossa.

```
source .venv/Scripts/activate
docker-compose up
streamlit run dashboard.py #Terminalissa 2
```


### 1. Datan päivitys (Inkrementaalinen)
Hakee vain uudet päivät Garminilta ja lisää ne olemassa oleviin tiedostoihin.
```bash
python fetch_garmin_data.py
```

### 2. Mallin koulutus
Lataa kaiken datan, prosessoi piirteet (uni, stressi, treenit, viiveet) ja kouluttaa XGBoost-mallin uudelleen.
```bash
python process_garmin_data.py
```
*Tämä päivittää myös `model_metrics.json`-tiedoston, joka näkyy dashboardissa.*

### 3. Dashboardin käynnistys
Avaa visuaalisen käyttöliittymän selaimessa (Localhost).
```bash
# Windows (CMD/PowerShell)
run_dashboard.bat

# Git Bash / Mac / Linux
streamlit run dashboard.py
```

---

## 2025-12-07 – Garmin-data & ensimmäinen malli
... (alkuperäinen sisältö säilyy, mutta tiivistettynä tässä näkymässä) ...

## 2025-12-08 – Hybrid AI Coach & Dashboard

Tänään projekti laajeni pelkästä ennustemallista täysiveriseksi valmennusjärjestelmäksi.

### 1. Dashboard (Streamlit)
- Rakensin visuaalisen käyttöliittymän (`dashboard.py`).
- **Refined Goal Features**:
    - **Back**: Updated `GoalCreate` model (`period_type`, `target_date`) and AI prompt context.
    - **Front**: Enhanced `AddGoalForm` with dynamic fields (Date Picker, Unit Dropdown) and better UX.

- **Dashboard Visualization**:
    - **Back**: Wired up `db_manager` (DuckDB) to new endpoints (`/readiness`, `/next-workout`).
    - **Front**: Built `StatCard` component and integrated metrics grid into the main dashboard.
    - **Qa**: Frontend build passed. Backend tests created but skipped due to local env issues.

- **Streamlit Migration (Feature Parity)**:
    - **Back**: Added endpoints for Manual Workouts (`/workouts/manual`), Data Refresh (`/system/refresh`), and History (`/plans/history`).
    - **Front**: Added "Log Workout" modal (form) and "Refresh Data" button to Dashboard.
    - **Front**: Added "Recent Coaching Plans" list.
    - **Migrated**: Essential features (refresh, manual log, history) are now providing parity with legacy `dashboard.py`.

- **Dashboard Visualizations (Phase 5)**:
    - **Performance**: Implemented CTL (Chronic Load), ATL (Acute Load), and TSB (Form) calculations using 42d/7d rolling averages.
    - **Charts**: Integrated `Recharts` to display visual trends for Recovery (Body Battery vs Sleep), Load, and Performance.
    - **Tech**: Backend uses `pandas` to process CSV history; Frontend uses `ResponsiveContainer`/`ComposedChart` for responsive analytics.
- Näkymän ominaisuudet:
    - **Päivän ennuste**: Body Battery -latausmittari.
    - **Treeniloki**: Graafit unesta, stressistä ja Body Batteryn kehityksestä (Plotly).
    - **Sidebar**: Näyttää datan tuoreuden ja mallin tarkkuuden (R²).

### 2. AI Coach (Gemini 2.5)
- Integroitu LLM-pohjainen valmentaja (`ai_coach.py`).
- **Generoi Treeniohjelma**:
    - Käyttäjä valitsee keston (1-7 päivää).
    - AI luo progressiivisen ohjelman, joka huomioi XGBoostin ennustaman vireystilan ja viimeaikaisen kuormituksen.
    - Ohjelma tallentuu `coach_history.json` -tiedostoon.
- **Trendianalyysi**:
    - Analysoi 30 päivän historian ja etsii korrelaatioita (esim. vaikuttaako stressi uneen).
    - Tallentuu `analysis_history.json` -tiedostoon.

### 3. Inkrementaalinen data
- Päivitin `fetch_garmin_data.py` -skriptin.
- Se ei enää lataa kaikkea dataa tyhjästä, vaan tarkistaa viimeisimmän tallennetun päivän ja hakee vain puuttuvat päivät.
- Tämä nopeuttaa päivittäistä käyttöä huomattavasti.

### Nykytilanne
- Data: 360 päivää historiaa.
- Malli: XGBoost (R² ~0.91).
- Coach: Gemini 2.5 Flash (Suomenkielinen).
- UI: Streamlit Web App.


### Joulukuu 8. - "The Great Restoration & Upgrade" 🛠️
*   **Kriisi:** Tärkeät tiedostot poistuivat vahingossa.
*   **Ratkaisu:** Palautimme kaiken (`dashboard.py`, `process_garmin_data.py`, jne.) "muistista" ja välimuistista.
*   **Päivitys (Model 2.0):**
    *   Malli rakennettiin uudelleen tyhjästä paremmaksi.
    *   Lisätty **Cross-Validation (TimeSeriesSplit)** ja **GridSearchCV**.
    *   Tulos: **R² 0.83** (MAE 3.80). Tämä on tieteellisesti validimpi kuin aiempi "haamu-0.91".
    *   **Feature Importance:** Tunnistettu tärkeimmät tekijät: `bodyBatteryHighestValue`, `bodyBatteryDuringSleep`.
*   **Dashboard:**
    *   Nimetty uudelleen: *"Sami's AI Coach"* 🏃
    *   Korjattu "loading state" -jumitus `st.empty()` ja `try-except` -logiikalla.
    *   Historiatrendit palautettu ja varmistettu.


## 2025-12-30 – Mallin päivitys ja analyysi

### Mallin tarkkuus
- **MAE (Mean Absolute Error):** 3.39
- **R² (Selitysaste):** 0.86

### Laatu ja Tulokset
Malli on tällä hetkellä erittäin laadukas. R²-arvo 0.86 tarkoittaa, että malli pystyy selittämään 86% Body Batteryn vaihtelusta, mikä on korkea luku fysiologiselle datalle. Keskimääräinen virhe (MAE) on vain n. 3.4 yksikköä.

Kuvista näemme:
1.  **Merkittävimmät tekijät:** Uusi `poor_night_flag` (huono yöuni) nousi heti tärkeimmäksi muuttujaksi. Tämä kertoo, että unen laadun raja-arvo (< 45 pistettä) on kriittinen päivän vireystilalle.
2.  **Ennustekyky:** Pisteparvivisualisointi osoittaa, että ennusteet seuraavat todellisia arvoja tiiviisti lineaarisesti.

![Feature Importance](Health_AI/outputs/feature_importance.png)
*(Mitkä tekijät vaikuttavat eniten)*

![Model Performance](Health_AI/outputs/model_performance.png)
*(Ennuste vs Todellinen - mitä lähempänä punaista viivaa pisteet ovat, sen parempi)*

## 2025-12-31 – UI Visuals & Calendar Uudistus 🖌️📅

Tänään keskityttiin käyttöliittymän modernisointiin ja käytettävyyden parantamiseen.

### 1. Kalenterinäkymä (`streamlit-calendar`)
- Lisättiin dashboardiin uusi "Kalenteri"-välilehti.
- Näyttää visuaalisesti tehdyt (Vihreä), väliin jätetyt (Punainen) ja tulevat treenit.
- Mahdollistaa treenihistorian hahmottamisen yhdellä silmäyksellä.

### 2. Visuaalinen ilme (UI/UX)
- Siirryttiin "Personal AI Coach" -brändäykseen.
- **Light Theme -ystävällinen design:**
    - Kortit muutettu valkoisiksi pehmeillä varjoilla.
    - Teksti tummanharmaata parhaan luettavuuden takaamiseksi.
    - Lisätty `structure-box` -elementti, joka korostaa treenin ytimen.
- **Taustakuva:** Lisätty `web_tausta.png` haaleana ja tyylikkäänä taustana (`linear-gradient` overlay), joka tuo sovellukseen syvyyttä ilman että se häiritsee lukemista.

Sovelus tuntuu nyt paljon enemmän modernilta web-sovellukselta kuin "pelkältä databoardilta". Seuraavaksi vuorossa tavoitteiden asettaminen! 🎯

### Phase 2: Intelligence & Goals (Tavoitteet & Älykkyys) 🧠🎯

Illan aikana toteutettiin ja viimeisteltiin Phase 2, joka toi sovellukseen tavoitteellisuuden.

**1. Tavoitteiden Asettaminen (Goal Setting):**
- Dashboardiin lisätty "Tavoitteet"-välilehti.
- Käyttäjä voi asettaa erityyppisiä tavoitteita: **Juoksu, Pyöräily, Uinti, Kuntosali** sekä määrällisiä tavoitteita (km/h).
- Tavoitteet tallentuvat DuckDB-tietokantaan (`goals`-taulu).

**2. Älykkyys (Intelligence Integration):**
- **Kontekstikietoisuus:** AI Coach (Gemini) hakee nyt aktiiviset tavoitteet ennen treeniohjelman luontia.
- **Lajikohtaisuus:** Jos tavoitteena on esim. "Pyöräily", prompti pakottaa tekoälyn painottamaan pyöräilyä treeniohjelmassa.
- **Palautejärjestelmä:** Treenien yhteydessä annettu palaute (Enemmän/Vähemmän näitä) syötetään tekoälylle, jotta se oppii käyttäjän mieltymykset.

Valmis kokonaisuus tukee nyt sekä datalähtöistä palautumista että tavoitteellista treenaamista.

### Phase 3: Data & Analytics (Data & Analytiikka) 📊
Laajennettiin sovellusta manuaalisella datalla ja analytiikalla.
- **Manuaalinen Kirjaus:** Lisätty mahdollisuus kirjata treenejä (esim. Hiihto, Kuntosali), jotka eivät olleet ohjelmassa.
- **Viikon Kuormitus:** Uusi graafi näyttää "Suunniteltu vs Tehty" -kuormituksen (Load Units = Kesto * Teho).
- **Tietokanta:** Päivitetty schema tukemaan tarkempaa seurantaa.

### Phase 4: Optimization (Optimointi - Etusivu) 🏠
Dashboardin rakenne uusittiin täysin käyttäjäystävällisemmäksi.
- **Uusi "Etusivu":** Kokoaa tärkeimmät tiedot (Body Battery, Uni, Seuraava treeni) yhteen näkymään.
- **Next Workout Card:** Näyttää selkeästi seuraavan harjoituksen tiedot heti avatessa.
- **Selkeys:** Välilehdet organisoitu loogisemmin (Etusivu, Ohjelma, Kalenteri, Kirjaa, Tavoitteet).

### Phase 5: CI/CD & Quality 🛡️
Projekti on nyt ammattimaisesti testattu ja automatisoitu.
- **GitHub Actions:** CI-putki ajaa automaattisesti lintauksen (Ruff) ja testit (Pytest) jokaisen Pushin yhteydessä.
- **Unit Tests (`tests/`):**
    - `test_backend.py`: Testaa tietokannan toiminnan (Tavoitteet, Treenien kirjaus).
    - `test_model.py`: "Smoke test" XGBoost-mallille (varmistaa että malli latautuu ja ennustaa).
    
Projekti on nyt erittäin kattava ja vakaa kokonaisuus! 🚀

### Phase 6: Production Readiness (Tuotantovalmius) 🏗️
Aloitettiin sovelluksen modernisointi kohti skaalautuvaa arkkitehtuuria.
- **Frontend/Backend jako:** Eriytettiin logiikka erilliseen `backend/` -sovellukseen (FastAPI).
- **Docker:** Backend on kontitettu ja ajetaan `docker-compose`:n avulla.
- **Hybrid Database:** Päätettiin pysyä vielä DuckDB:ssä, mutta backend lukee sitä jaetun Docker-volumen kautta (`/data/health_ai.db`).
- **Dashboard:** Etusivun näkymät (Seuraava treeni, Viikkokuorma, Aktiiviset Tavoitteet) hakevat nyt datan **Firestoresta** API:n kautta.
- **Security:** Lisätty Rate Limiting (`slowapi`) ja Service Account Key -hallinta.

Projekti on nyt "Hybrid Cloud" -tilassa: Kriittinen uusi data (Tavoitteet) on pilvessä, vanha data (Treenihistoria) on lokaalisti. 🌩️🏠

Tämä mahdollistaa tulevaisuudessa Frontendin vaihtamisen (esim. React/Mobiili) ilman, että logiikkaan tarvitsee koskea.



## 2026-01-02 – Backend Security Hardening 🔒

Tänään varmistettiin backendin tietoturva "Production Readiness" -hengessä. Koska siirrymme monen käyttäjän malliin, datan eristäminen on kriittistä.

### 1. Firebase Authentication
- Implementoitu `AuthMiddleware` (`auth_middleware.py`), joka tarkistaa jokaisesta API-kutsusta Bearer-tokenin.
- Token validoidaan Firebase Admin SDK:lla. Virheellisestä tokenista seuraa välitön 401 Unauthorized.

### 2. Data Isolation (`user_id`)
- Päivitetty `firestore_manager.py` niin, että *jokainen* tietokantahaku sisältää pakollisen `where('user_id', '==', uid)` -filtterin.
- Tämä estää sen, että käyttäjä A voisi vahingossa (tai tahallaan) nähdä käyttäjän B treenejä.

### 3. Verifikaatio
Luotiin automaattiset testiskriptit (`backend/tests/`) ja ajettiin ne onnistuneesti:
- `verify_firestore_isolation.py`: Simuloi "tunkeilijaa" ja varmisti, että hänelle ei palauteta dataa.
- `verify_api_auth.py`: Pommitti API:a ilman tokenia ja varmisti, että portit pysyvät kiinni.

Tietoturva on nyt kunnossa backendin puolella. 🛡️

## 2026-01-02 – Frontend: Next.js & Firebase Auth ⚛️🔥

Iltapäivällä siirryimme Frontendiin (`web`-kansio).

### 1. Perusrakenne (Scaffolding)
- Asennettiin Next.js, TailwindCSS, ja tarvittavat kirjastot (`firebase`, `lucide-react`).
- Konfiguroitiin `.env.local` Firebase-avaimilla.

### 2. Autentikaatio (Auth Context)
- Luotiin React Context (`AuthContext.tsx`), joka:
    - Hallinnoi käyttäjän tilaa (User | null).
    - Tarjoaa `signInWithGoogle` -funktion.
    - Kuuntelee `onAuthStateChanged` -tapahtumia.

### 3. Integraatio Backendin kanssa
- Backend vaati CORS-asetukset (`localhost:3000` sallittu).
- Dashboard kutsuu nyt backendiä (`/goals`) käyttäjän ID-tokenilla (`Authorization: Bearer <token>`).
- **Tulos:** Frontti ja Backki juttelevat keskenään turvallisesti! 🎉

### Lopetustoimet & Seuraavat askeleet
- **Tietoturvatarkistus:** Varmistettu, että `.gitignore` sulkee pois `.env`, `.env.local`, ja `service_account_key.json` -tiedostot. Secrets ovat turvassa eikä niitä mene GitHubiin.
- **Seuraavat askeleet:**
    1.  Toteutetaan frontendille "Lisää tavoite" -lomake, jotta saamme dataa tietokantaan.
    2.  Parannetaan Dashboardin ulkoasua.


## 2026-01-05 – Full Stack Feature: Add Goals & Start-up Fixes 🎯

Tänään saimme ensimmäisen "Full Stack" -toiminnallisuuden valmiiksi, jossa data kulkee käyttöliittymästä tietokantaan asti.

### 1. Add Goal -toiminnallisuus
Käyttäjä voi nyt luoda uusia tavoitteita suoraan Dashboardilta.
- **Backend:**
    - Luotu endpoint `POST /goals`.
    - `firestore_manager.py`: Lisätty `add_goal`-funktio, joka tallentaa tavoitteen Firestoreen käyttäjän ID:llä eristettynä.
- **Frontend:**
    - `AddGoalForm.tsx`: Moderni lomake tavoitteiden syöttämiseen (Laji, Määrä, Yksikkö).
    - Integroitu Dashboardiin niin, että lista päivittyy heti lisäyksen jälkeen ilman sivun latausta.

### 2. Laadunvarmistus
- Kirjoitettu `backend/tests/test_endpoints.py`, joka testaa API:n toiminnan.
- Testit käyttävät **Mockingia**, eli ne eivät vaadi oikeaa tietokantayhteyttä toimiakseen. Tämä nopeuttaa kehitystä ja CI-putkea.

### 3. Bugikorjaukset & Käytettävyys
- **Porttikorjaus:** Frontend yritti kutsua porttia `8001`, mutta Docker pyörii portissa `8000`. Tämä korjattiin configiin.
- **Käynnistys:** Selkeytettiin, että Next.js-frontend ajetaan `web`-kansiossa komennolla `npm run dev` ja backend `docker-compose up`.

### 4. Vianetsintä & Viimeistely
- **Data Refresh**: Korjattu ongelma, jossa "Refresh"-nappi ei päivittänyt tietoja. Syynä oli puuttuvat ympäristömuuttujat (`.env`) Dockerissa ja väärä työhakemisto (`CWD`) skriptejä ajettaessa. Korjattu pakottamalla polku `/data`-kansioon.
- **Riippuvuudet**: Lisätty puuttuvat kirjastot (`pandas`, `garminconnect`, `xgboost`) Docker-konteineriin.
- **UX**: Lisätty selitteet ("hover tooltips") kuvaajille ja korjattu asetteluongelma, jossa kuvaajat menivät päällekkäin.

### 5. AI Insights (Phase 6)
- **Ominaisuus**: Päivittäinen AI-valmentaja ("Your Personal AI Coach is ready for you") Dashboardin yläreunassa.
- **Tekoäly**: Käyttää Gemini API:a analysoimaan TSB:n (vireystila), Body Batteryn ja unidataa.
- **Backend**: Uusi endpoint `/ai/insight`, joka laskee kontekstin ja kutsuu `ai_coach.py`. Lisätty Rate Limiting (`slowapi`) ja dynaaminen polunhaku kirjastolle.
- **Frontend**: Näyttävä `AIInsightCard` komponentti, jossa on latausanimaatiot ja virheenkäsittely.

## 2026-01-06 – SDK Migration, Goal Management & Calendar Polish 🛠️📅

Tänään tehtiin merkittäviä parannuksia sovelluksen vakauteen ja käytettävyyteen.

### 1. SDK Migraatio (`google-generativeai` -> `google-genai`)
- **Ongelma:** Vanha `google-generativeai` SDK on deprecated ja aiheutti varoituksia.
- **Ratkaisu:** Siirryttiin uuteen `google-genai` SDK:hon. Päivitetty `ai_coach.py` käyttämään uutta Client API:a. Tämä varmistaa yhteensopivuuden tulevaisuudessa.

### 2. Training Calendar (Next.js)
- Rakennettiin moderni kalenterinäkymä (`TrainingCalendar.tsx`) suoraan Next.js:ään käyttäen `date-fns`:ää.
- **Modal Popup:** Työkaluvihjeet korvattiin tyylikkäällä modaali-ikkunalla, joka näyttää treenin tarkemmat tiedot (sis. "Structure" eli "15 min lämmittely...").
- **Visuaalisuus:** Historia (Vihreä) vs Suunniteltu (Sininen) erottuvat selkeästi.

### 3. Goal Management (Active Goals)
- **Täysi CRUD:** Tavoitteita voi nyt **lisätä, muokata ja poistaa** suoraan Dashboardilta.
- **UX Parannukset:**
    - "Active Goals" -korttiin lisätty Edit/Delete -ikonit (näkyvät hoveratessa).
    - Tavoitepäivämäärät ("Target Date") näkyvät nyt oikein.
    - Uusi `AddGoalForm` tukee sekä luontia että muokkausta.

### 4. AI Plan Logic (Overwrite Fix)
- Korjattiin logiikka, jossa uusi AI-ohjelma ei ylikirjoittanut vanhoja "Pending"-treenejä.
- **Backend:** Lisätty `delete_pending_workouts` -funktio `firestore_manager.py`:hyn.
- **Optimointi:** Tietokantahaku optimoitiin toimimaan ilman monimutkaisia indeksejä (Composite Index) tekemällä filtteröinti muistissa.


## 2026-01-07 – Bugit, Mobiili & Workout Logging 📱🐛

Tänään oli "huoltopäivä", joka päättyi uuteen ominaisuuteen.

### 1. Kriittiset Bugikorjaukset
- **Firebase Auth Error:** Korjattu `INVALID_API_KEY` ja `auth/unauthorized-domain` virheet.
    - Syy: `.env.local` tiedostossa avaimet oli väärin (JSON-muodossa vs KEY=VALUE) ja Domain-whitelist puuttui.
- **Tailwind Ei Toiminut:** Korjattu `Can't resolve 'tailwindcss'` build-virhe.
    - Syy: Kotihakemistossa (`~`) oli "haamu" `package.json`, joka sekoitti Next.js:n (Turbopack) polut.
    - Ratkaisu: Poistettu haamutiedostot ja tehty puhdas asennus (`clean install`).

### 2. Mobiilikäyttö (Local Network)
- **Ongelma:** Kännykällä ei päässyt sovellukseen (`connection refused`).
- **Ratkaisu:**
    - Firewall: Avattu portit `3000` (Frontend) ja `8000` (Backend).
    - Config: Vaihdettu kuunteluosoitteet `0.0.0.0`.
    - Auth: Lisätty kodin IP Whitelistiin Firebase-konsolissa.
- Nyt sovellus toimii Wi-Fi -verkossa millä tahansa laitteella!

### 3. Workout Logging (Dual Write) 🏋️‍♂️
- Lisätty mahdollisuus kirjata manuaalisia treenejä Next.js Dashboardista.
- **Dual Write Strategia:** Datan eheyden takaamiseksi (koska olemme migraatiovaiheessa), uudet treenit tallennetaan **kahteen paikkaan**:
    1.  **DuckDB (Legacy):** Jotta vanha `dashboard.py` (Streamlit) näkee ne ja trendit eivät katkea.
    2.  **Firestore (Modern):** Tulevaisuuden skaalautuvaa backendia varten.
- **UI:** Lisätty tyylikäs tumma modaali-ikkuna (`ManualWorkoutForm`) kirjausta varten.

### 4. User Menu (UI/UX) 🍔
- Lisätty Dashboardin oikeaan yläkulmaan "Hampurilais-valikko".
- Sisältää selkeät toiminnot: *Profile, Settings, Sign Out*.
- Korvaa aiemman yksittäisen "Sign Out" -napin, säästäen tilaa ja parantaen yleisilmettä.

Projekti on nyt taas raiteillaan ja valmiina seuraaviin ominaisuuksiin! 🚀


## 2026-01-08 – Calendar Drag & Drop & Regeneration 📅✨

Tänään Training Calendarista tehtiin aidosti interaktiivinen työkalu.

### 1. Drag & Drop (Siirrä & Järjestä)
- Implementoitu `@dnd-kit/core` kirjastolla.
- **PointerSensor:** Vaihdettu `MouseSensor` -> `PointerSensor`, jotta kosketusnäytöt (mobiili/tabletti) toimivat luotettavasti.
- **Live Update:** Kun treenin pudottaa uudelle päivälle, Backend päivittää päivämäärän ja UI päivittyy välittömästi ilman sivun latausta.
- **Visuals:** Raahattava kortti ("Overlay") näyttää nyt identtiseltä alkuperäisen kanssa, eikä ole vain "Moving..." tekstilaatikko.

### 2. Trash Can (Roskakori) 🗑️
- Kalenterin alareunaan ilmestyy roskakori, kun käyttäjä alkaa raahata treeniä.
- **Drop to Delete:** Treenin voi pudottaa roskikseen, jolloin avautuu vahvistusikkuna.

### 3. Smart Regeneration (Älykäs Korvaus) 🤖
- Kun treenin poistaa, käyttäjä voi valita: "Delete Only" tai **"Regenerate"**.
- **Regenerate-logiikka:**
    1.  Vanha treeni poistetaan.
    2.  Lähetetään pyyntö AI:lle (`/plans/generate`), jossa kerrotaan *mikä* treeni hylättiin ("Rejected Plan Details").
    3.  AI luo uuden, paremmin sopivan treenin tilalle.
- **Rajoitus:** Estetty spämmäys päivittäisellä 5 pyynnön katolla (`check_daily_generation_limit`).

### 4. Backend (API Expansion)
- `PATCH /workouts/{id}`: Päivämäärän muuttamiseen.
- `DELETE /workouts/{id}`: Yksittäisen treenin poistoon.
- `POST /plans/generate`: Päivitetty hyväksymään `rejected_plan_details` kontekstiksi.

Nyt kalenteri ei ole vain *näkymä*, vaan *työkalu* viikon suunnitteluun! 🚀

