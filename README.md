# Personal AI Coach 🏃‍♂️🤖

**Personal AI Coach** on älykäs, dataohjautuva valmennusjärjestelmä, joka auttaa optimoimaan palautumista ja harjoittelua.

Se yhdistää:
1.  **Garmin-datan** (uni, stressi, sykevariabiliteetti).
2.  **Machine Learning -mallin (XGBoost)**, joka ennustaa päivän vireystilan (Training Readiness / Body Battery).
3.  **Generatiivisen tekoälyn (Google Gemini)**, joka toimii henkilökohtaisena valmentajana ja luo päivittäiset treenisuositukset datan perusteella.

## Ominaisuudet
*   **Älykäs Dashboard:** Reaaliaikainen näkymä palautumisen tilasta ja treenihistoriasta.
*   **Treenikalenteri:** Visuaalinen yleisnäkymä menneisiin ja tuleviin harjoituksiin.
*   **Adaptiivinen AI Coach:** Valmentaja, joka huomioi väsymyksen ja muokkaa ohjelmaa dynaamisesti (esim. keventää treeniä huonosti nukutun yön jälkeen).
*   **Tavoitteellisuus:** Aseta tavoitteita (Juoksu, Pyöräily, Uinti, Kuntosali) ja AI rakentaa ohjelman tukemaan niitä.
*   **Tarkka Ennustemalli:** Omatuntoon perustuvaa arviota tarkempi koneoppimismalli vireystilan arviointiin.

## Teknologiat
*   **Frontend:** Streamlit, Plotly, Streamlit Calendar
*   **Backend / AI:** Python, XGBoost, Google Gemini API
*   **Tietokanta:** DuckDB

## Käynnistys
Aja projektin juuressa:
```bash
streamlit run dashboard.py
```
