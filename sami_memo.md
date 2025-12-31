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


