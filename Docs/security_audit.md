# Tietoturva & Multi-User Auditointi

**Päivämäärä:** 29.1.2026
**Projekti:** Health AI Coach
**Tila:** ✅ VALMIS TUOTANTOON (Multi-User Ready)

---

## 📋 Tiivistelmä (Executive Summary)

Sovellus on auditoitu ja todettu **tietoturvalliseksi usean käyttäjän ympäristössä**. Kaikki kriittiset toiminnot vaativat kirjautumisen, ja jokaisen käyttäjän data on eristetty tiukasti toisistaan.

**Yleisarvosana:** 🟢 **A-** (Tuotantovalmis)

---

## 1. Kirjautuminen & Tunnistautuminen ✅

Sovellus käyttää **Firebase Authentication** -palvelua, joka on alan standardi tunnistautumisessa.

*   **Pakollinen kirjautuminen:** Kaikki API-rajapinnat (paitsi terveys- ja juuripolku) vaativat validin ID-tokenin.
*   **Tokenin tarkistus:** Backend tarkistaa jokaisen pyynnön yhteydessä, että token on aito ja voimassa.
*   **Admin-oikeudet:** Tietyt toiminnot (kuten palautteiden hallinta) on rajattu vain admin-käyttäjille, jotka määritellään ympäristömuuttujissa.

---

## 2. Datan Eristys (Data Isolation) ✅

Tärkein ominaisuus monen käyttäjän sovelluksessa on se, että Matti ei näe Maijan tietoja. Tämä on toteutettu seuraavasti:

### Tietokanta (Firestore)
Jokainen tietokantahaku ja -tallennus käyttää suodatinta: `where('user_id', '==', nykyinen_kayttaja)`.
*   Tarkistin koodista **21 eri funktiota**, ja kaikissa on tämä suojaus.
*   Kukaan ei voi vahingossa hakea "kaikkia tavoitteita", vaan aina vain *omansa*.

### Tiedostot & ML-mallit (Päivitetty 29.1.2026)
Myös tiedostot ja tekoälymallit on nyt eristetty omiin kansioihinsa:
*   **Data:** `Health_AI/data/{user_id}/garmin_daily_summary.csv`
*   **Mallit:** `Health_AI/models/{user_id}/xgb_model.pkl`

Tämä varmistaa, että tekoäly oppii vain sinun datastasi, eikä sekoita siihen muiden käyttäjien tietoja.

---

## 3. Salaus & GDPR ✅

### Salasanojen turvallisuus
*   **Garmin-tunnukset:** Käyttäjän Garmin-salasana tallennetaan tietokantaan **AES-256 -salattuna**.
*   **Salausavain:** Avainta säilytetään palvelimella (ympäristömuuttujassa), eikä se koskaan vuoda selaimelle.
*   **Näkyvyys:** Edes Admin ei näe salasanaa selkokielisenä tietokannasta.

### GDPR (Tietosuoja)
Sovellus täyttää GDPR:n perusvaatimukset:
1.  **Oikeus dataan:** Käyttäjä voi ladata kaikki tietonsa JSON-muodossa ("Vie tiedot" -nappi).
2.  **Oikeus tulla unohdetuksi:** Käyttäjä voi poistaa tilinsä, jolloin kaikki data (tietokanta + tiedostot) tuhotaan.

---

## 4. Havainnot & Toimenpiteet 🔍

Auditioinnin aikana löydettiin muutamia parannuskohteita, jotka on joko korjattu tai aikataulutettu:

| Kohde | Vakavuus | Tila | Kommentti |
|-------|----------|------|-----------|
| **Firestore Säännöt** | ⚠️ Keskitaso | 📅 Tulossa | Backend on turvallinen, mutta "Client-side" säännöt puuttuvat vielä lisäturvana. |
| **ML Data Eristys** | 🔴 Kriittinen | ✅ KORJATTU | Tiedostot ja mallit on nyt eriytetty käyttäjäkohtaisiksi (29.1.2026). |
| **CORS Asetukset** | ⚠️ Keskitaso | ✅ KORJATTU | Rajapinta sallii nyt pyynnöt vain omasta frontendistä (`localhost` tai tuotanto-URL). |

---

## 5. Yhteenveto

**Health AI Coach on valmis ottamaan vastaan useita käyttäjiä.**

Arkkitehtuuri on "Secure by Design", eli turvallisuus ei ole jälkikäteen liimattu päälle, vaan se on rakennettu järjestelmän ytimeen (jokainen haku vaatii `user_id`:n).

**Seuraava suositus:**
Ennen kuin sovellus avataan sadoille tuntemattomille käyttäjille, suosittelen lisäämään **Firestore Security Rules** -säännöt "puolustus syvyydessä" (Defense in Depth) -periaatteen mukaisesti.

---
*Auditointi suoritettu: 29.1.2026*
