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
        WebFrontend[Next.js App<br/>web/]
    end

    %% Backend Services
    subgraph "Backend Services"
        FastAPI[FastAPI<br/>backend/]
        Firestore[(Firestore<br/>Cloud DB)]
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
    User <-->|Vuorovaikutus| WebFrontend
    
    WebFrontend <-->|REST API / Auth| FastAPI
    FastAPI <-->|Write/Read| Firestore
    
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
*   **CSV-tiedostot (`Health_AI/data/`):** Pääasiallinen raakadatan varasto. Sisältää päivittäiset yhteenvedot, unidataa ja aktiviteetit.
*   **DuckDB (`health_ai.db`):** Lokaali tietokanta historialliselle datalle ja treeniohjelmille.
*   **Firestore (Cloud):** Käyttäjäkohtainen pilvitietokanta. Säilyttää tavoitteet (`goals`) ja tulevaisuuden dataa. Turvattu Security Ruleilla.

### 2. Machine Learning Core (Älykkyys)
*   **Backend API (`backend/`):** FastAPI-palvelin, joka toimii porttina kaikelle uudelle toiminnallisuudelle.
    *   **Auth:** Firebase ID Token verifikaatio middlewarena.
    *   **Endpoints:** `/goals`, `/next-workout`, jne.
*   **Datan haku (`fetch_garmin_data.py`):** Inkrementaalinen lataus Garmin Connectista.
*   **Mallinnus (`process_garmin_data.py`):** XGBoost-mallin koulutus ja ylläpito.
*   **AI Coach (`ai_coach.py`):** Kommunikoi Google Gemini API:n kanssa.

### 3. Application Layer (Käyttöliittymä)
*   **Web Frontend (`web/`):** Moderni Next.js -sovellus (React).
    *   Toimii pääasiallisena käyttöliittymänä tavoitteiden hallintaan.
    *   Viestii Backend API:n kanssa (Port 8000).
*   **Dashboard (`dashboard.py`):** (Legacy/Admin) Streamlit-näkymä syvälliseen data-analyysiin.

## Teknologia-stack
*   **Kieli:** Python 3.12, TypeScript
*   **ML:** XGBoost, Scikit-learn
*   **AI:** Google Gemini 2.5 Flash
*   **Backend:** FastAPI, Firebase Admin SDK
*   **Frontend:** Next.js, TailwindCSS
*   **Data:** Pandas, DuckDB, Firestore
*   **Infra:** Docker, Docker Compose
