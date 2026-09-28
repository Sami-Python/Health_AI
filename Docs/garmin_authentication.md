# Garmin-autentikointi

**Päivitetty:** Huhtikuu 2026  
**Status:** Tuotannossa ✅

## Yleiskuvaus

Health AI käyttää Garmin-integraatiossa yhdistelmää, joka takaa vakaan ja turvallisen autentikoinnin:

- **`curl_cffi`** – HTTP-asiakaskirjasto, joka käyttää standardeja selainyhteensopivia TLS-profiileja
- **`garminconnect` + `garth`** – Virallinen Python-integraatiokirjasto OAuth1/OAuth2-tokenien hallintaan
- **Android SSO -flow** – Kirjautuminen Garminin mobiili-API:n kautta, joka on vakaampi kuin web-pohjainen SSO
- **AES-256 -salaus** – Käyttäjätunnukset tallennetaan Firestoreen AES-256-CBC-salauksella

## Arkkitehtuuri

```
Käyttäjä → /garmin/connect (backend)
    ↓
1. Tarkistetaan olemassaolevat OAuth-tokenit (Firestore)
    ↓ (jos tokenit puuttuvat tai vanhentuneita)
2. Autentikointi Garmin SSO:n kautta (Android mobile API)
    ↓
3. OAuth1 Service Ticket → OAuth2 Token Exchange
    ↓
4. Tokenit tallennetaan AES-256-salattuna Firestoreen
    ↓
Seuraavat kutsut: Token resume (ei uutta kirjautumista)
```

## Token-hallinta

- **Tallennus:** `garth.dump()` → tilapäishakemiston kautta → Firestore-dokumentti (salattu)
- **Lataus:** Firestore → tilapäishakemisto → `garth.login(tokenstore=tmpdir)`
- **Uusiminen:** Proaktiivinen `garth.refresh()` ennen jokaista data-hakua
- **Cooldown:** Firestore-pohjainen rate-limit cooldown (60 min) suojaa liialta kirjautumisyrityksiltä

## Rate Limit -käsittely

Garmin asettaa API-kirjautumiselle rate limitin. Sovellus käsittelee tämän:

1. **Cooldown-rekisteri** – Firestoreen tallennetaan `rate_limit_until`-kenttä
2. **Token resume etusijalla** – Olemassaolevat tokenit käytetään ennen uutta kirjautumista
3. **Selkeä käyttäjäpalaute** – Sovellus näyttää odotusajan UI:ssa
4. **Admin-endpoint** – `POST /garmin/clear-cooldown` tyhjentää cooldownin tarvittaessa

## 2FA / MFA

Jos Garmin vaatii 2FA-vahvistuksen:

1. Backend tunnistaa `GarminMFARequiredError`-poikkeuksen
2. Käyttäjälle lähetetään push-ilmoitus (Firebase Cloud Messaging)
3. Mobiilisovelluksessa näkyy punainen varoitusbanneri
4. Käyttäjä syöttää 2FA-koodin Profiilinäkymässä

## Vianmääritys

| Virhe | Todennäköinen syy | Toimenpide |
|-------|-------------------|------------|
| `401 Unauthorized` | Tokenit vanhentuneita | Reconnect Profiili-sivulta |
| `429 Too Many Requests` | Rate limit aktiivinen | Odota cooldown-aika |
| `403 Forbidden` | SSO-istunto kadonnut | Uusi kirjautuminen |
| `MFA Required` | Garmin vaatii 2FA | Syötä koodi sovelluksessa |

Lisätietoja asennuksesta: [garmin_setup.md](garmin_setup.md)
