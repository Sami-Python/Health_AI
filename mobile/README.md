# Health AI Mobile 📱

Mobiilisovellus Health AI -palvelulle. Rakennettu Flutterilla.

## Ominaisuudet
- **Dashboard:** Päivän metriikat, kuormitus ja Garmin-yhdistys.
- **Kalenteri:** Treenien siirrot, poistot, AI-uudelleenaikataulutus sekä manuaalinen kirjaus.
- **AI Chat Coach:** Personoitu keskustelu fysiologisen datasi ja tavoitteidesi pohjalta.
- **Authentication:** Google Sign-In, 2FA/MFA tuettu Garmin, GDPR-hallinnointi.
- **UI/UX:** Moderni Glassmorphism-design, tumma teema (Slate 950), Pull-to-Refresh tuki.

## Teknologiat
- **Flutter & Dart** (v3.41.2+)
- **State Management:** `setState` & `FutureBuilder`
- **Backend Integraatio:** REST API (FastAPI) Bearer-token authilla
- **Tietoturva:** Firebase Auth + Cleartext lokaaliin testaukseen

## Kehitys & Käynnistys

Varmista, että tietokoneesi backend on käynnissä, ennen kuin käynnistät applikaation (esim. `uvicorn main:app --host 0.0.0.0 --reload`).

**Verkon ja IP-osoitteen asettaminen:**
Jos ajat sovellusta fyysisellä Android- / iOS-laitteella, sinun täytyy kertoa sovellukselle tietokoneesi oikea paikallinen IP-osoite, sillä puhelin on eri "laitteella" kuin tietokoneesi "localhost".
1. Tarkista tietokoneesi IP-osoite (Windows: `ipconfig`, Mac: `ifconfig`). *Esim. WiFi verkossa 192.168.1.130, Hotspotissa 172.20.10.4*.
2. Päivitä osoite laitteesi `mobile/lib/core/services/api_service.dart` tiedostoon muuttujaan `baseUrl`.

```bash
# Asenna riippuvuudet
flutter pub get

# Käynnistä (valitse kytketty fyysinen laite)
flutter run
```
