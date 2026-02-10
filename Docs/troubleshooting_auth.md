# Google Authentication Troubleshooting Guide

Tämä dokumentti auttaa ratkaisemaan yleisimmät Google Sign-In -ongelmat Health AI -tuotantoympäristössä (`app.personalaicoach.ai`).

## 1. Yleiset Virheet ja Ratkaisut

### Virhe: `auth/api-key-not-valid`
**Oire:** Kirjautumisikkuna vilahtaa tai ei aukene, konsolissa punainen virhe.
**Syy:** API-avain on väärä, poistettu tai sillä on vääriä rajoituksia.
**Ratkaisu:**
1.  Tarkista `frontend/.env.production` tiedoston `NEXT_PUBLIC_FIREBASE_API_KEY`.
2.  Mene Google Cloud Console → APIs & Services → Credentials.
3.  Varmista, että käytössä oleva Browser key:
    -   Ei ole poistettu.
    -   Ei rajoita HTTP-refererejä väärällä domainilla. Sallittujen listalta tulee löytyä: `app.personalaicoach.ai/*`.
4.  Jos avain on vaihdettu: Päivitä `.env.production`, aja `npm run build`, ja julkaise uudelleen.

### Virhe: `auth/unauthorized-domain`
**Oire:** Google-kirjautumisikkuna ei aukea, tai se sulkeutuu heti virheilmoituksella.
**Syy:** Tuotantodomain ei ole sallittujen listalla Firebase Authentication -asetuksissa.
**Ratkaisu:**
1.  Mene Firebase Console → Authentication → Settings → Authorized domains.
2.  Lisää: `app.personalaicoach.ai`.
3.  Lisää myös (jos haluat staging-testauksen): `staging-url.cloudflare.pages.dev`.

### Virhe: `auth/popup-blocked`
**Oire:** Selain estää kirjautumisikkunan avautumisen.
**Syy:** Selaimen popup-estäjä on aktiivinen.
**Ratkaisu:**
-   Ohjeista käyttäjää sallimaan popupit sivustolla `app.personalaicoach.ai`.
-   **Vaihtoehto**: Vaihda `signInWithRedirect` -metodiin (ei vaadi popupia). Tämä vaatii koodimuutoksen `AuthContext.tsx`:ssä.

## 2. Debug-työkalut

### Selaimen kehittäjätyökalut (F12):
-   **Console-välilehti**: Näyttää Firebase-virhekoodit.
-   **Network-välilehti**: Suodata `identitytoolkit` nähdäksesi Googlen auth-pyynnöt ja niiden vastaukset.
-   **Application → IndexedDB → firebaseLocalStorage**: Näet tallennetun käyttäjätiedon ja tokenin.

### Hyödylliset konsoli-komennot (Tuotantoselaimessa):
```javascript
// Tarkista onko käyttäjä kirjautunut:
firebase.auth().currentUser

// Hae nykyinen token:
await firebase.auth().currentUser?.getIdToken(true)
```

## 3. Eskalointiprosessi

Jos yllä olevat eivät ratkaise ongelmaa:
1.  Tarkista Firebasen status: [status.firebase.google.com](https://status.firebase.google.com)
2.  Katso Firebasen tunnettuja ongelmia: [Firebase Release Notes](https://firebase.google.com/support/releases)
3.  Mikäli ongelma vaikuttaa palvelinpuolelta: Tarkista `backend/` lokit Cloud Runissa (Google Cloud Console → Cloud Run → Logs).
