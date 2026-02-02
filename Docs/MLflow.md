# 🧪 MLflow for MLOps

**MLOps** (Machine Learning Operations) on käytäntöjä, jotka tekevät ML-malleista tuotannoksi valmaat. **MLflow** on avoimen lähdekoodin työkalu, joka auttaa sinua seuraamaan malli-eksperimenttejä, versioida malleja ja yhtenäistää deployment-prosessia.

---

## 📋 Sisällysluettelo

1. [Mikä on MLflow?](#mika-on-mlflow)
2. [Miksi käytämme MLflow:ta?](#miksi-kaytamme-mlflowta)
3. [Asennus](#asennus)
4. [Käyttö: Mallin Treenaaminen](#kaytto-mallin-treenaaminen)
5. [MLflow UI](#mlflow-ui)
6. [Eksperimenttien Vertailu](#eksperimenttien-vertailu)
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

### Ongelma Ilman MLOps:ia

Ilman MLflow:ta et tiedä:
- ❓ Mikä mallin versio on tuotannossa?
- ❓ Mitkä hyperparametrit tuottivat parhaan tuloksen?
- ❓ Onko mallin suorituskyky heikentynyt ajan myötä?

### Ratkaisu MLflow:n kanssa

- ✅ **Versiointi**: Näet kaikki treenit ja niiden parametrit
- ✅ **Metriikat**: Vertaile R², MAE, RMSE -arvoja graafisesti
- ✅ **Artifacts**: Tallenna feature importance, plotit, mallit
- ✅ **Reproducibility**: Toista mikä tahansa treenaus täsmälleen

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

## Käyttö: Mallin Treenaaminen

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

#### 1. **Experiments-näkymä**
- Listaa kaikki treenit (`xgboost_readiness_prediction`)
- Näyttää jokaisen runin:
  - **Run ID**: Uniikki tunniste
  - **Metrics**: R², MAE, RMSE
  - **Parameters**: Hyperparametrit
  - **Duration**: Treenaus kesti

#### 2. **Run Details**
Klikkaa mitä tahansa руниa nähdäksesi:
- **Parameters**: Kaikki hyperparametrit
- **Metrics**: Numeerinen ja graafinen näkymä
- **Artifacts**: Lataa feature importance, plotit, mallit

#### 3. **Compare Runs**
- Valitse 2+ run:ia
- Klikkaa "Compare"
- Näet:
  - Parallel Coordinates Plot (parametrit vs metriikat)
  - Scatter Matrix
  - Taulukon eroista

---

## Eksperimenttien Vertailu

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
   - Näet 3 run:ia
   - Klikkaa "R2" -sarake että järjestät parhaimmasta huonoimpaan
   - **Tulos:** Esim. `learning_rate=0.03` → R²=0.87 (paras)

3. **Lataa paras malli:**
   - Klikkaa parasta run:ia
   - Artifacts → `xgboost_model` → Lataa mallin tai deployaa

---

## Model Registry

### Mikä on Model Registry?

MLflow **Model Registry** on keskitetty paikka, jossa:
- Versionkoitu mallit ovat (v1, v2, v3...)
- Malleille annetaan **stage** (Staging, Production, Archived)

### Mallin Rekisteröinti

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

#### 1. **Loka ali Development (Nykyinen)**
- MLflow UI ajaa lokaalisti (`localhost:5000`)
- SQLite database `backend/data/mlflow.db`
- **Käyttö:** Debugging, eksperimentit

#### 2. **Cloud Deployment (Tulevaisuus)**

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

#### 3. **Model Serving (API)**

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

### Ongelma: UI ei näytä run:eja

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

## 🎯 Best Practices

### 1. **Nimeä Experimentit Selkeästi**
```python
mlflow.set_experiment("xgboost_readiness_v2_tuning")
```

### 2. **Tagaa Run:it**
```python
mlflow.set_tags({
    "model_type": "xgboost",
    "environment": "development",
    "engineer": "sami"
})
```

### 3. **Logita Kaikki Relevantit Parametrit**
- Älä rajoitu vain hyperparametreihin
- Logita myös: `data_version`, `feature_count`, `user_id` (jos multi-user)

### 4. **Säännöllinen Cleanup**
- Vanhoja run:eja voi poistaa UI:sta ("Delete Run")
- Säilytä vain parhaat ja production-mallit

### 5. **Käytä Model Registry Tuotannossa**
- Älä viittaa run ID:hen (`runs:/abc123/model`)
- Käytä nimiä ja stageja (`models:/my_model/Production`)

---

## 🔗 Aiheeseen Liittyvät Dokumentit

- [arkkitehtuuri.md](arkkitehtuuri.md) - ML Core -arkkitehtuuri
- [Backend Scripts](file:///c:/Users/samih/code/health_ai/backend/scripts/process_garmin_data.py) - Treenausskripti
- [MLflow Official Docs](https://www.mlflow.org/docs/latest/index.html)

---

## 📊 Yhteenveto

| Toiminto | Komento/URL |
|----------|-------------|
| **Treenaa Malli** | `python scripts/process_garmin_data.py --user-id UID` |
| **Käynnistä UI** | `mlflow ui --backend-store-uri sqlite:///data/mlflow.db` |
| **Avaa UI** | http://localhost:5000 |
| **Database** | `backend/data/mlflow.db` |
| **Experiment Name** | `xgboost_readiness_prediction` |

---

**Viimeksi päivitetty:** 2026-01-29  
**Dokumentaation kattavuus:** Experiment Tracking, Model Registry, Local Deployment  
**TODO:** Cloud Deployment (Cloud Run, Vertex AI), A/B Testing, Drift Detection


![alt text](image.png)