# 🚀 Quick Start
Tässä komennot projektin ajamiseen. Varmista, että olet oikeassa kansiossa.

```
source .venv/Scripts/activate
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
python -m streamlit run dashboard.py
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

Järjestelmä on nyt vakaampi kuin koskaan. "Lessons learned": Parempi versionhallinta (Git) olisi estänyt sydämentykytykset!
