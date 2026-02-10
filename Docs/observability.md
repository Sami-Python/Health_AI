# Observability & Monitoring

Tämä sivu kuvaa Health AI Coach -järjestelmän valvonta-, virheenseuranta- ja tietoturvaominaisuudet.

## 1. Google Cloud Error Reporting

Backend (`backend/`) on integroitu **Google Cloud Error Reporting** -palveluun.

- **Käyttö:** Tuotantoympäristössä (`APP_ENV=production`).
- **Toiminta:** Kun backendissä tapahtuu käsittelemätön poikkeus (500 Internal Server Error), stack trace ja virheilmoitus lähetetään automaattisesti Google Cloudiin.
- **Hyödyt:** Kehittäjät saavat reaaliaikaisen ilmoituksen (esim. sähköpostitse) kriittisistä kaatumisista.

## 2. Logging Infrastructure

Sovellus käyttää strukturoitua JSON-lokia, joka on yhteensopiva Google Cloud Loggingin kanssa.

### Structured Logging
- **Kirjasto:** `python-json-logger`
- **Format:** JSON
- **Kentät:** `timestamp`, `severity` (INFO/WARN/ERROR), `message`, `module`, `trace_id`

### Request Tracing
Jokainen HTTP-pyyntö lokitetaan automaattisesti middlewaren toimesta:
- **Tiedot:** Method, Path, Status Code, Duration (ms), IP-osoite.
- **Konfiguraatio:** `backend/main.py` -> `RequestLoggingMiddleware`

## 3. Rate Limit Monitoring

Sovellus käyttää `slowapi`-kirjastoa API:n kuormituksen rajoittamiseen. Olemme lisänneet näkyvyyttä siihen, kuka rajoituksiin osuu.

- **Persistent Logging:** Kaikki "429 Too Many Requests" -tapahtumat tallennetaan Firestoreen (`security_events` -kokoelma).
- **Tallennetut tiedot:**
    - `ip`: Pyynnön tekijän IP-osoite.
    - `path`: Endpoint, jota yritettiin kutsua (esim. `/ai/generate-plan`).
    - `limit`: Rikottu raja (esim. "50/minute").
    - `timestamp`: Tapahtuman aika.
    - `user_agent`: Laitteen/selaimen tiedot.

### Admin Dashboard (Security)

Frontendin Admin-näkymässä (`/admin`) on **Security**-välilehti, josta ylläpitäjä voi tarkastella näitä logeja reaaliajassa.

## 4. Session Management (Security)

Tietoturvan parantamiseksi järjestelmässä on mekanismit epäilyttävien istuntojen hallintaan.

### Force Logout (Admin)

Jos ylläpitäjä havaitsee väärinkäytöksiä (esim. Rate Limit -logeista), hän voi pakottaa käyttäjän uloskirjautumisen.

- **Toiminto:** Admin Dashboard -> Users -> "Force Logout".
- **Tekninen toteutus:** Kutsuu `/admin/revoke-tokens/{uid}` endpointia.
- **Vaikutus:** Mitätöi käyttäjän Firebase Refresh Tokenin. Käyttäjä ei voi enää uusia ID-tokeniaan (joka vanhenee tunnissa), ja joutuu kirjautumaan uudelleen sisään.

## 5. Audit Trail

Kaikki merkittävät tietoturvatapahtumat, mukaan lukien adminien tekemät toimenpiteet (kuten käyttäjien poistaminen tai logien katselu), tallennetaan `security_events` -kokoelmaan.

### Log Schema (`security_events`)
```json
{
  "type": "rate_limit_exceeded | auth_failure | admin_access",
  "ip": "1.2.3.4",
  "path": "/api/endpoint",
  "limit": "50/minute (optional)",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "Firestore Timestamp"
}
```

## 6. Performance Monitoring (Prometheus & Grafana)

Kehitystä ja valvontaa varten järjestelmään on integroitu Prometheus-tilastot.

### Käynnistys
Koska monitorointikontit ovat raskaita, ne on eriytetty omaan tiedostoonsa. Pääset monitorointiin käsiksi ajamalla:

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitor.yml up
```

### Palvelut:
*   **Prometheus:** `http://localhost:9090` – Kerää datan.
*   **Grafana:** `http://localhost:3001` – Dashboard.
    *   **User:** `admin`
    *   **Pass:** `admin`
    *   **Setup:** Lisää Data Source "Prometheus" osoitteella `http://prometheus:9090` (internal docker network).

### Metric Data (`/metrics`)
Backend tarjoaa automaattisesti metriikkaa osoitteessa `/metrics`. Prometheus käy hakemassa ("Scrape") tämän 15 sekunnin välein.

Mitatut suureet:
*   **http_requests_total:** Pyyntöjen kokonaismäärä.
*   **http_request_duration_seconds:** Vasteajat.
*   **process_cpu_seconds:** Backendin prosessorikuorma.

## 7. Admin User Management

Admin Dashboard sisältää **Users**-välilehden, joka tarjoaa kokonaiskuvan kaikista rekisteröityneistä käyttäjistä.

### Backend Endpoint
- **Endpoint:** `GET /admin/users`
- **Authentication:** Admin-only (`verify_admin` middleware)
- **Data Source:** Firebase Authentication + Firestore
- **Response:**
  - User ID (UID)
  - Email address
  - Display name (if set)
  - Account status (Active/Disabled)
  - Garmin connection status
  - Creation timestamp
  - Last sign-in timestamp

### Frontend Component
- **Component:** `UsersTable.tsx`
- **Location:** Admin Dashboard → Users tab
- **Features:**
  - Sortable table with user metadata
  - Status badges (Active/Disabled, Garmin Connected/Disconnected)
  - **Force Logout** button – Revokes user's refresh tokens
  - Refresh button to reload user list
  - Loading skeletons for better UX

### Use Cases
- **User Support:** Quickly identify user issues (e.g., Garmin not connected)
- **Security:** Monitor account activity and force logout suspicious sessions
- **Analytics:** Track user growth and engagement (last login times)
- **Debugging:** Verify user account status during troubleshooting
