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

    %% Firebase Platform
    subgraph "Firebase Platform"
        FirebaseAuth[Authentication]
        Firestore[("Firestore DB<br/>User Data / Goals")]
    end

    %% Data Layer
    subgraph "Legacy Data Layer"
        Fetcher[fetch_garmin_data.py]
        CSV[("CSV Tiedostot<br/>backend/data/")]
        DuckDB[("DuckDB<br/>backend/data/health_ai.db")]
    end

    %% Machine Learning Core
    subgraph "AI & ML Core"
        Processor[process_garmin_data.py]
        XGB_Model[XGBoost Model]
        Predictor[predict_readiness.py]
        CoachLogic[ai_coach.py]
    end

    %% Moderni Käyttöliittymä
    subgraph "Modern UI (Next.js)"
        UI_Login[Login / Auth]
        UI_Dashboard[Dashboard Page]
        UI_Charts["Recharts<br/>(Discovery, Load, Performance)"]
        UI_AICard[AI Insight Card]
    end

    %% Backend Services
    subgraph "Backend API"
        FastAPI[FastAPI Service]
    end

    %% Data Flow - External
    Garmin -->|JSON| Fetcher
    Fetcher -->|Tallentaa| CSV

    %% ML Flow
    CSV -->|Opetusdata| Processor
    Processor -->|Kouluttaa| XGB_Model
    
    %% Backend Intergration
    FastAPI -->|Lue Historia| CSV
    FastAPI -->|Lue/Kirjoita| Firestore
    FastAPI -->|Trigger| Fetcher
    FastAPI -->|Generoi| CoachLogic
    
    CoachLogic -->|Prompt| Gemini
    
    %% UI Integration
    User -->|Kirjautuu| UI_Login
    UI_Login -.->|Token| FirebaseAuth
    
    User -->|Selaa| UI_Dashboard
    UI_Dashboard -->|Render| UI_Charts
    UI_Dashboard -->|Render| UI_AICard
    
    UI_Dashboard <-->|"API Calls (Bearer Token)"| FastAPI
    FastAPI -.->|Verify Token| FirebaseAuth

    %% Legacy Support
    UI_Dashboard -.->|Legacy Data| DuckDB

![alt text](image-1.png)

## Komponentit

### 1. Moderni Käyttöliittymä (Next.js)
*   **Kehitysportaali (`frontend/`):** React-pohjainen sovellus, joka tarjoaa rikkaan käyttökokemuksen.
    *   **Dashboard:** Päänäkymä, joka kokoaa kaiken tiedon.
    *   **Goal Management:** Tavoitteiden hallinta (CRUD) ja Race-tavoitteet.
    *   **Training Calendar:** Interaktiivinen kalenteri (Drag & Drop) treenien suunnitteluun.
    *   **Recharts / Sparklines:** Interaktiiviset kuvaajat ja minitrendit korteissa.
    *   **AI Insight Card:** Päivittäinen yhteenveto tekoälyltä.
    *   **Authentication:** Firebase Auth -integraatio sisäänkirjautumiseen.

### 2. Firebase Platform (Pilvipalvelut)
*   **Authentication:** Hallinnoi käyttäjien identiteettiä ja turvallisuutta (JWT).
*   **Firestore:** NoSQL-tietokanta, joka säilyttää käyttäjän tavoitteet (`goals`) ja asetukset reaaliaikaisesti.

### 3. Backend & AI Core (Älykkyys)
*   **Backend API (`backend/`):** FastAPI-palvelin, joka orkestroi liikenteen UI:n, tietokantojen ja AI-mallien välillä.
*   **Backend Scripts (`backend/scripts/`):** Datan haku- ja käsittelyscriptit (ETL).
*   **AI Coach (`backend/ai_coach.py`):** Yhdistää fysiologisen datan Gemini 2.5 -kielimalliin. **Sisältää välimuistin (Firestore Cache)** API-kiintiöiden hallintaan.
*   **Machine Learning:** XGBoost-mallit ennustavat tulevaa valmiustilaa (`readiness`) historian perusteella.

### 4. Data Layer (Tietovarasto)
*   **CSV-tiedostot (`backend/data/`):** Toimii edelleen "Totuuden lähteenä" historialliselle Garmin-datalle.
*   **Legacy Sync:** `main.py` synkronoi automaattisesti Garmin-datan CSV:stä Firestoreen, jotta Dashboard pysyy ajan tasalla.
*   **Dual Write:** Uudet manuaaliset treenit kirjoitetaan sekä DuckDB:hen että Firestoreen.


## Teknologia-stack
*   **Frontend:** Next.js 14, React, Recharts, Tailwind CSS
*   **Backend:** Python 3.10 (FastAPI), Pandas, XGBoost
*   **AI/ML:** Google Gemini 2.5 Flash, XGBoost Regressor
*   **Data:** CSV (Legacy), DuckDB, Firestore
*   **Infra:** Docker Compose
