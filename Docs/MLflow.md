# MLflow for MLOps

**MLOps** (Machine Learning Operations) on käytäntöjä, jotka tekevät ML-malleista tuotantovalmiita. **MLflow** on avoimen lähdekoodin työkalu, joka auttaa seuraamaan malli-eksperimenttejä, versioimaan malleja ja yhtenäistämään deployment-prosessia.

---

## Sisällysluettelo

1. [Mikä on MLflow?](#mika-on-mlflow)
2. [Miksi käytämme MLflow:ta?](#miksi-kaytamme-mlflowta)
3. [Asennus](#asennus)
4. [Käyttö: Mallin treenaaminen](#kaytto-mallin-treenaaminen)
5. [MLflow UI](#mlflow-ui)
6. [Eksperimenttien vertailu](#eksperimenttien-vertailu)
7. [Model Registry](#model-registry)
8. [Tuotantokäyttö](#tuotantokaytto)
9. [Troubleshooting](#troubleshooting)

---

## Mikä on MLflow?

**MLflow** on alusta, joka auttaa ML-elinkaaren hallinnassa. Se tarjoaa:

- **Experiment Tracking**: Logita parametrit, metriikat ja tulokset jokaisesta treenistä
- **Model Registry**: Versiointi ja hallinta malleille
- **Reproducibility**: Toista kaikki treenit identtisesti
- **Deployment**: Yksinkertaista deployment-prosessia

**Tässä projektissa:** MLflow seuraa XGBoost-mallin treenejä, vertailee eri hyperparametreja ja tallentaa parhaat mallit.

---

## Miksi käytämme MLflow:ta?

### Ongelma ilman MLOps:ia

Ilman MLflow:ta et tiedä:
- Mikä mallin versio on tuotannossa?
- Mitkä hyperparametrit tuottivat parhaan tuloksen?
- Onko mallin suorituskyky heikentynyt ajan myötä?

### Ratkaisu MLflow:n kanssa

- **Versiointi**: Näet kaikki treenit ja niiden parametrit
- **Metriikat**: Vertaile R², MAE, RMSE -arvoja graafisesti
- **Artifacts**: Tallenna feature importance, plotit, mallit
- **Reproducibility**: Toista mikä tahansa treenaus täsmälleen

---

## Asennus

MLflow on jo lisätty `backend/requirements.txt`:iin. Asenna komennolla:

```bash
cd backend
pip install -r requirements.txt
```

**Tarkista asennus:**
```bash
mlflow --version
# Expected: mlflow, version 2.10.0 tai uudempi
```

---

## Käyttö: Mallin treenaaminen

### Scriptissä: `process_garmin_data.py`

MLflow on integroitu suoraan treenausskriptiin. Kun ajat:

```bash
cd backend
python scripts/process_garmin_data.py --user-id YOUR_UID
```

**Mitä tapahtuu taustalla:**

1. **MLflow Experiment luodaan**: `xgboost_readiness_prediction`
2. **Run käynnistyy**: Uusi ID jokaiselle treenille
3. **Parametrit logitetaan**:
   - Hyperparametrit: `n_estimators`, `learning_rate`, `max_depth`
   - Data split: `test_size`, `cv_splits`
4. **Metriikat logitetaan**:
   - `r2_score`, `mae`, `rmse`
   - `train_samples`, `test_samples`, `total_features`
5. **Artifacts logitetaan**:
   - Trained model (`.pkl` ja MLflow format)
   - Feature importance (JSON + PNG)
   - Model performance plot (PNG)

### Koodiesimerkit

**MLflow Run -contexti:**
```python
with mlflow.start_run():
    # Log hyperparameters
    mlflow.log_params({
        "n_estimators": 100,
        "learning_rate": 0.03,
        "max_depth": 5
    })
    
    # Train model
    model.fit(X_train, y_train)
    
    # Log metrics
    mlflow.log_metrics({
        "r2_score": 0.87,
        "mae": 5.2,
        "rmse": 6.8
    })
    
    # Log model
    mlflow.sklearn.log_model(model, "xgboost_model")
    
    # Log artifacts (plots, JSONs)
    mlflow.log_artifact("feature_importance.png", "plots")
```

---

## MLflow UI

### Käynnistäminen

MLflow tallentaa datan SQLite-tietokantaan `backend/data/mlflow.db`. Käynnistä UI:

```bash
cd backend
mlflow ui --backend-store-uri sqlite:///data/mlflow.db
```

**Avaa selaimessa:**
```
http://localhost:5000
```

### UI:n Toiminnot

#### 1. Experiments-näkymä
- Listaa kaikki treenit (`xgboost_readiness_prediction`)
- Näyttää jokaisen runin:
  - **Run ID**: Uniikki tunniste
  - **Metrics**: R², MAE, RMSE
  - **Parameters**: Hyperparametrit
  - **Duration**: Treenauksen kesto

#### 2. Run Details
Klikkaa mitä tahansa runia nähdäksesi:
- **Parameters**: Kaikki hyperparametrit
- **Metrics**: Numeerinen ja graafinen näkymä
- **Artifacts**: Lataa feature importance, plotit, mallit

#### 3. Compare Runs
- Valitse 2+ runia
- Klikkaa "Compare"
- Näet:
  - Parallel Coordinates Plot (parametrit vs metriikat)
  - Scatter Matrix
  - Taulukon eroista

---

## Eksperimenttien vertailu

### Esimerkkiskenaario

**Tavoite:** Mikä `learning_rate` antaa parhaan R²?

1. **Aja 3 treeniä eri learning rateilla:**
   ```bash
   # Muokkaa param_grid process_garmin_data.py:ssä
   'learning_rate': [0.01, 0.03, 0.05]
   
   # Aja:
   python scripts/process_garmin_data.py --user-id YOUR_UID
   ```

2. **MLflow UI:ssa:**
   - Avaa `xgboost_readiness_prediction` experiment
   - Näet 3 runia
   - Klikkaa "R2" -sarake järjestääksesi parhaimmasta huonoimpaan
   - **Tulos:** Esim. `learning_rate=0.03` → R²=0.87 (paras)

3. **Lataa paras malli:**
   - Klikkaa parasta runia
   - Artifacts → `xgboost_model` → Lataa mallin tai deployaa

---

## Model Registry

### Mikä on Model Registry?

MLflow **Model Registry** on keskitetty paikka, jossa:
- Versioidut mallit ovat (v1, v2, v3...)
- Malleille annetaan **stage** (Staging, Production, Archived)

### Mallin rekisteröinti

**Option 1: UI:ssa**
1. Avaa run jonka haluat rekisteröidä
2. Artifacts → `xgboost_model`
3. Klikkaa "Register Model"
4. Nimeä: `xgboost_readiness_model`
5. Version: Automaattinen (v1, v2...)

**Option 2: Koodissa**
```python
# process_garmin_data.py:ssä
mlflow.sklearn.log_model(
    best_model, 
    "xgboost_model",
    registered_model_name="xgboost_readiness_model"
)
```

### Staget (Production Flow)

```
Staging → Production → Archived
```

**Esimerkki:**
1. Treenaa uusi malli → Rekisteröi → **Staging**
2. Testaa staging-malli testiympäristössä
3. Jos toimii → Siirrä **Production**
4. Vanha malli → **Archived**

---

## Tuotantokäyttö

### Skenaariot

#### 1. Lokaali Development (Nykyinen)
- MLflow UI ajaa lokaalisti (`localhost:5000`)
- SQLite database `backend/data/mlflow.db`
- **Käyttö:** Debugging, eksperimentit

#### 2. Cloud Deployment (Tulevaisuus)

**Option A: MLflow Tracking Server (Cloud Run):**
```yaml
# docker-compose.prod.yml
mlflow-server:
  image: python:3.12-slim
  command: mlflow server --backend-store-uri postgresql://... --host 0.0.0.0
  ports:
    - "5000:5000"
```

**Option B: Google Vertex AI:**
- Integroi MLflow → Vertex AI Experiments
- Automaattinen scaling, managed cloud storage

#### 3. Model Serving (API)

Lataa tuotantomalli MLflow:sta:
```python
# backend/main.py tai erillinen model loader
import mlflow.sklearn

model_uri = "models:/xgboost_readiness_model/Production"
loaded_model = mlflow.sklearn.load_model(model_uri)

# Käytä ennusteisiin:
prediction = loaded_model.predict(X_new)
```

---

## Troubleshooting

### Ongelma: `mlflow: command not found`

**Syy:** MLflow ei ole asennettu aktiiviseen ympäristöön

**Ratkaisu:**
```bash
cd backend
source ../.venv/Scripts/activate  # tai ../.venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
```

---

### Ongelma: UI ei näytä runeja

**Syy:** Väärä tracking URI

**Ratkaisu:**
```bash
# Tarkista että käynnistät UI oikealla polulla:
cd backend
mlflow ui --backend-store-uri sqlite:///data/mlflow.db

# HUOM: Polku on relatiivinen CWD:hen, joten aja AINA backend/-kansiosta
```

---

### Ongelma: `PermissionError` kun logittaa artifacteja

**Syy:** Ei kirjoitusoikeuksia `backend/data/` tai `Health_AI/outputs/`

**Ratkaisu:**
```bash
# Luo kansiot:
mkdir -p backend/data
mkdir -p Health_AI/outputs

# Dockerissa: Varmista että volume on mounted oikein
docker-compose down
docker-compose up -d
```

---

### Ongelma: Metriikat näkyvät, mutta ei artifacteja

**Syy:** Artifactit eivät ole ladattu MLflow:een

**Debug:**
```python
# Tarkista process_garmin_data.py:ssä että:
mlflow.log_artifact(fi_png_path, "plots")  # Polku on oikea
```

**Testaa polussa:**
```bash
ls Health_AI/outputs/feature_importance.png
# Jos tiedostoa ei ole, plotting ei toiminut
```

---

### Ongelma: `SQLite IntegrityError / is_nan` kaatumiset

**Syy:** Jos `process_garmin_data.py` saa liian pienen datasetin (esim. 1 päivän Incremental-päivitys Cloud Runissa), R2, MAE tai RMSE saattaa evaluoitua `NaN` -arvoksi (Not a Number) ohjelmassa. MLflow ja sen taustalla oleva SQLite-tietokanta menee lukkoon, mikäli se yrittää tallentaa `NaN` tyyppejä tietokantatauluun `log_metric` tai `log_metrics` käskyillä.

**Ratkaisu:** Varmista aina koulutusskripteissä pandas-kirjaston `pd.isna(metric)` suojapiirit ennen MLflown kutsua. (Toteutettu ohjelmaan 28.2.2026: NaN-arvot korvataan float-nollilla (`0.0`), jolloin asennus ei kaadu).

---

## Best Practices

### 1. Nimeä Experimentit selkeästi
```python
mlflow.set_experiment("xgboost_readiness_v2_tuning")
```

### 2. Tagaa runit
```python
mlflow.set_tags({
    "model_type": "xgboost",
    "environment": "development",
    "engineer": "sami"
})
```

### 3. Logita kaikki relevantit parametrit
- Älä rajoitu vain hyperparametreihin
- Logita myös: `data_version`, `feature_count`, `user_id` (jos multi-user)

### 4. Säännöllinen cleanup
- Vanhoja runeja voi poistaa UI:sta ("Delete Run")
- Säilytä vain parhaat ja production-mallit

### 5. Käytä Model Registryä tuotannossa
- Älä viittaa run ID:hen (`runs:/abc123/model`)
- Käytä nimiä ja stageja (`models:/my_model/Production`)

---

## Aiheeseen liittyvät dokumentit

- [arkkitehtuuri.md](arkkitehtuuri.md) – ML Core -arkkitehtuuri
- [Backend Scripts](file:///c:/Users/samih/code/health_ai/backend/scripts/process_garmin_data.py) – Treenausskripti
- [MLflow Official Docs](https://www.mlflow.org/docs/latest/index.html)

## Tuotantokäyttö (Cloud Run & Paikallinen)

### 1. MLflow-rajoittaminen Tuotannossa (Cloud Run Optimointi)
Pilviympäristössä (kuten Cloud Run) levylle kirjoittaminen ja prosessiin sitomattomien tausta-ajojen pyörittäminen voi syödä resursseja (`Memory`/`CPU`). Tästä syystä `process_garmin_data.py` on optimoitu siten, että:

1. **MLflow on OLETUKSENA POIS PÄÄLTÄ** nopeuttamaan ajoa.
2. Välitetään R² / MAE pisteet ja malli kuitenkin suoraan Firestoreen reaaliajassa, mutta ei generoida plotti-kuvia.
3. Jos teet kokeita paikallisesti, ota se käyttöön lipulla:
   ```bash
   # Windows PowerShell
   $env:MLFLOW_ENABLED="true"; python scripts/process_garmin_data.py --user-id YOUR_UID
   
   # Linux/Mac
   MLFLOW_ENABLED=true python scripts/process_garmin_data.py --user-id YOUR_UID
   ```

### 2. CSV -> Parquet -päivitys
Mallin ominaisuusmatriisi (Feature matrix) pakataan nyt `.csv` -tekstitiedoston sijaan nopeammin latautuvaan ja kompressoituun **Parquet** (`.parquet`) -muotoon polkuun:
`backend/data/garmin_merged_features.parquet`

---

**Viimeksi päivitetty:** 2026-03-04  
**Dokumentaation kattavuus:** Experiment Tracking, Model Registry, Local Deployment, Cloud Cost Opt.