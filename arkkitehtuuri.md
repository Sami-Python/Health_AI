# Arkkitehtuuri - Sami's AI Coach

## Järjestelmän Yleiskuva
Sami's AI Coach on datalähtöinen valmennusjärjestelmä, joka yhdistää Garminin fysiologisen datan, koneoppimisen (XGBoost) ennustemallit ja generatiivisen tekoälyn (Gemini 2.5) tarjotakseen personoitua palautumisanalyysiä ja treenisuosituksia.

## Arkkitehtuurikaavio (Mermaid)

```mermaid
graph TD
    %% Ulkoiset Palvelut
    Garmin((Garmin Connect API))
    Gemini((Gemini 2.5 AI))
    User((Käyttäjä))

    %% Data Layer
    subgraph "Data Layer"
        Fetcher[fetch_garmin_data.py]
        CSV[(CSV Tiedostot<br/>Health_AI/data/)]
        DuckDB[(DuckDB<br/>health_ai.db)]
        Secrets[.env<br/>Salaisuudet]
    end

    %% Koneoppiminen & Logiikka
    subgraph "Machine Learning Core"
        Processor[process_garmin_data.py]
        XGB_Model[XGBoost Model<br/>Health_AI/models/*.pkl]
        Predictor[predict_readiness.py]
        CoachLogic[ai_coach.py]
        Analyst[Jupyter Notebooks]
    end

    %% Käyttöliittymä
    subgraph "Application Layer"
        Dashboard[dashboard.py<br/>Streamlit UI]
    end

    %% Data Flow
    Garmin -->|JSON/Raw| Fetcher
    Secrets -.-> Fetcher
    Secrets -.-> CoachLogic
    Fetcher -->|Tallentaa| CSV
    
    CSV -->|Opetusdata| Processor
    Processor -->|Kouluttaa| XGB_Model
    Processor -->|Generoi kuvat| Dashboard
    
    CSV -->|Lukee historiaa| Predictor
    XGB_Model -->|Lataa mallin| Predictor
    
    %% UI Flow
    User <-->|Vuorovaikutus| Dashboard
    Dashboard -->|Hakee ennusteen| Predictor
    Dashboard -->|Pyytää neuvoa| CoachLogic
    
    CoachLogic -->|Prompt + Context| Gemini
    Gemini -->|Treeniohjelma| CoachLogic
    
    CoachLogic -->|Tallentaa ohjelman| DuckDB
    Dashboard <-->|Lukee/Kirjoittaa| DuckDB
    
    Analyst -->|Tutkii/Kehittää| XGB_Model
```

![alt text](image.png)

## Komponentit

### 1. Data Layer (Tietovarasto)
*   **CSV-tiedostot (`Health_AI/data/`):** Pääasiallinen raakadatan varasto. Sisältää päivittäiset yhteenvedot, unidataa ja aktiviteetit. Helppo lukea Pandasilta.
*   **DuckDB (`health_ai.db`):** Kevyt, tiedostopohjainen SQL-tietokanta. Käytetään generoitujen treeniohjelmien ja coachin neuvojen pysyvään tallennukseen ja historiaan.
*   **Secret Management (`.env`):** Säilyttää API-avaimet (Garmin, Gemini) turvallisesti poissa koodista.

### 2. Machine Learning Core (Älykkyys)
*   **Datan haku (`fetch_garmin_data.py`):** Inkrementaalinen lataus Garmin Connectista. Hakee vain puuttuvat päivät.
*   **Mallinnus (`process_garmin_data.py`):**
    *   **Preprocessing:** Datan puhdistus, yhdistäminen ja "Feature Engineering" (esim. `poor_night_flag`, liukuvat keskiarvot).
    *   **Training:** XGBoost Regressor -mallin koulutus `GridSearchCV`:llä ja aikasarja-ristivalidoinnilla (TimeSeriesSplit).
    *   **Output:** Tallentaa mallin (`.pkl`) ja analyysikuvat (`.png`).
*   **Ennustaminen (`predict_readiness.py`):** Itsenäinen moduuli, joka lataa mallin ja uusimman datan antaakseen ennusteen dashboardille.
*   **AI Coach (`ai_coach.py`):** Kommunikoi Google Gemini API:n kanssa. Rakentaa dynaamisia prompteja perustuen käyttäjän fysiologiseen tilaan (Body Battery, Stressi, Unen laatu).

### 3. Application Layer (Käyttöliittymä)
*   **Dashboard (`dashboard.py`):** Streamlitillä rakennettu verkkosovellus.
    *   Näyttää reaaliaikaiset mittarit ja ennusteet.
    *   Visualisoi trendit interaktiivisilla graafeilla (Plotly).
    *   Tarjoaa käyttöliittymän AI Coachille treeniohjelmien luontiin.
    *   Sisältää "Model Analysis" -näkymän mallin laadun tarkkailuun.

## Teknologia-stack
*   **Kieli:** Python 3.12
*   **ML:** XGBoost, Scikit-learn, SHAP
*   **AI:** Google Gemini 2.5 Flash
*   **Data:** Pandas, DuckDB
*   **Visualisointi:** Plotly, Matplotlib, Seaborn
*   **Backend/Frontend:** Streamlit
*   **Infra:** Windows, Python Virtual Environment (`.venv`)
