# Google Authentication Troubleshooting Guide

Tämä dokumentti auttaa ratkaisemaan yleisimmät Google Sign-In -ongelmat Health AI -tuotantoympäristössä (`app.personalaicoach.ai`).

## 1. Yleiset Virheet ja Ratkaisut

### Virhe: `auth/api-key-not-valid`
**Oire:** Kirjautumisikkuna vilahtaa tai ei aukene, konsolissa punainen virhe.
**Syy:** API-avain on väärä, poistettu tai sillä on vääriä rajoituksia.
**Ratkaisu:**
1.  Tarkista `frontend/.env.production` tiedoston `NEXT_PUBLIC_FIREBASE_API_KEY`.
2.  Varmista Google Cloud Consolessa (Credentials), että avain on olemassa.
3.  **Application Restrictions:** Pitää olla `Websites` ja sisältää `https://app.personalaicoach.ai`.

### Virhe: `auth/popup-closed-by-user` (Vaikka et sulkenut)
**Oire:** Popup aukeaa, lataa hetken ja sulkeutuu.
**Syy:** Google ei luota domainiin, josta kutsu tulee.
**Ratkaisu:**
1.  **Firebase Console > Authentication > Settings > Authorized Domains:**
    - Lisää `app.personalaicoach.ai`.
2.  **Google Cloud Console > Credentials > OAuth 2.0 Client IDs > Web client:**
    - **Authorized JavaScript origins:** Lisää `https://app.personalaicoach.ai` (ja `https://www.personalaicoach.ai`).

### Virhe: `403 Forbidden` (getProjectConfig)
**Oire:** Verkkovirhe (Network tab) `identitytoolkit` tai `getProjectConfig` -kutsussa.
**Syy:** API-avaimen *API Restrictions* estää käytön.
**Ratkaisu:**
1.  Google Cloud Console > Credentials > API Key.
2.  Aseta **API restrictions** tilaan **Don't restrict key** (helpoin korjaus).
3.  TAI salli erikseen: `Identity Toolkit API` ja `Token Service API`.

### Virhe: `401 Unauthorized` (Backend)
**Oire:** Kirjautuminen onnistuu frontendissa, mutta data ei lataudu (Dashboard tyhjä).
**Syy:** Token on vanhentunut tai backendin Firebase-projekti on eri kuin frontendin.
**Ratkaisu:**
1.  Kirjaudu ulos ja takaisin sisään (päivittää tokenin).
2.  Varmista, että `backend/config.py` `FIREBASE_PROJECT_ID` vastaa frontendin asetusta.

## 2. Oikeat Asetukset (Referenssi)

### Frontend (`.env.production`)
```env
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy... (Uusi, toimiva avain)
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=personal-ai-coach-92c39.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=personal-ai-coach-92c39
```

### Google Cloud Console
- **Project:** `personal-ai-coach-92c39`
- **Credentials > API Key:**
  - Application restrictions: `https://app.personalaicoach.ai`, `http://localhost:3000`
  - API restrictions: `Don't restrict` (tai Identity Toolkit + Token Service)
- **Credentials > OAuth 2.0 Client ID:**
  - Authorized JavaScript origins: `https://app.personalaicoach.ai`

### Firebase Console
- **Authentication > Authorized domains:** `app.personalaicoach.ai`
