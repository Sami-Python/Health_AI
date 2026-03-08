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

### Virhe: `auth/unauthorized-domain` tai `auth/requests-from-referer-are-blocked`
**Oire:** Google-kirjautumisikkuna ei aukea, tai se sulkeutuu heti virheilmoituksella, jossa mainitaan estetty referer (esim. `personalaicoach-app.pages.dev`).
**Syy:** Uusi tuotantodomain (kuten Cloudflare Pages -osoite) ei ole sallittujen listalla **joko** Firebasessa tai Google Cloud Platformissa. Tämän täytyy täsmätä molemmissa!

**Ratkaisu (2 Vaihetta):**

**Vaihe 1: Firebase Console (Sallitut verkkotunnukset)**
1. Mene Firebase Console → Authentication → Settings → Authorized domains.
2. Klikkaa "Add domain" ja lisää verkkotunnus täsmällisesti (esim. `personalaicoach-app.pages.dev`).
3. Varmista että myös varsinainen päädomain `app.personalaicoach.ai` on listalla.

**Vaihe 2: Google Cloud Console (OAuth 2.0 Web Client)**
1. Mene Google Cloud Console → APIs & Services → Credentials.
2. Etsi "OAuth 2.0 Client IDs" -listauksesta Web-asiakas (esim. *Web client (auto created by Google Service)*).
3. Rullaa alas asetusnäkymässä kohtaan **"Authorized JavaScript origins"**.
4. Klikkaa "ADD URI" ja liitä sinne kyseinen uusi osoite (esim. `https://personalaicoach-app.pages.dev`). Anna muodossa `https://...` ilman perässä olevaa vinoviivaa `/`.
5. Tallenna.
6. **Huom:** Tässä saattaa kestää 2-5 minuuttia astua voimaan. Tyhjennä selaimen välimuisti ja kokeile uudelleen.

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
