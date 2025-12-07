## 2025-12-08 – Garmin-data & ensimmäinen malli

- Rakensin `fetch_garmin_data.py`-skriptin, joka:
	- lukee Garmin-tunnukset `.env`:stä
	- hakee viimeisen ~90 päivän päivätason datan `get_stats`-kutsulla → `garmin_daily_summary.csv`
	- hakee päivittäisen sykkeen `get_heart_rates`-kutsulla → `garmin_hr_timeseries.csv` (raaka JSON per päivä)
- Notebook `garmin_analysis.ipynb`:
	- luen ja visualisoin päivätason datan (askeleet, kalorit, body battery, hengitys)
	- parsitaan HR-raaka JSON → `df_hr_ts` (timestamp + bpm + resting/max/min HR)
	- lasketaan yöajan (00–05/06) sykevaihtelua kuvaava mittari `bpm_std_night` per päivä
	- yhdistetään yö-HR-mittari päivätason datan kanssa → `df_merged`
	- tutkitaan trendejä (7d liukuvat keskiarvot) ja scatterit kuorman vs yö-HR:n välillä
- Rakensin XGBoost-regressiomallin ennustamaan seuraavan päivän `bodyBatteryChargedValue`-arvoa.
	- Tulos: MAE ~12, R2 ~0 → malli ei vielä opi hyödyllistä signaalia.
	- Johtopäätös: tarvitsen lisää ja parempia piirteitä (uni, oikea HRV, treenit), sekä enemmän päiviä.

Seuraavat mahdolliset jatkoaskeleet:
- lisätä `fetch_garmin_data.py`-skriptiin unen (`get_sleep_data`) ja treenien (`get_activities`) haku
- rakentaa per-päivä uni- ja treenitunnusluvut (sleep_minutes, deep_sleep, workout_minutes jne.) ja yhdistää ne `df_merged`:iin
- kokeilla uudestaan yksinkertaista mallia (esim. XGBoost / RandomForest) uusilla piirteillä tai käyttää mallia enemmän feature-tutkimukseen kuin ennustukseen

virtuaaliympäristö
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows


