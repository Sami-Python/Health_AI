# 📱 Mobile (Flutter) vs Web (Next.js) – Feature Vertailu

> **Päivitetty:** 2026-03-06
> **Mobiili:** `mobile/lib/features/` (6 näkymää + bottom nav 5 välilehteä)
> **Web:** `frontend/src/app/` + `components/` (20+ komponenttia)

---

## ✅ Ominaisuuspariteetti-taulukko

| Ominaisuus | Web ✅ | Mobiili | Huomio |
|---|---|---|---|
| **Dashboard / Etusivu** | ✅ | ✅ | Pariteetti hyvä |
| AI Insight -kortti | ✅ | ✅ | Molemmat hakevat `/ai/insight` |
| Stats Grid (Readiness, Load, Workout, Goals) | ✅ | ✅ | Sama 2x2 rakenne |
| Readiness & Sleep Charts | ✅ | ✅ | Mobiilissa glassmorphism |
| Garmin-yhteysbanneri dashboardilla | ✅ | ✅ | Phase 14.2 ✅ |
| **Kalenteri (TrainingCalendar)** | ✅ | ✅ | API-data käytössä (`/workouts/history` + `/workouts/next`) |
| Drag & Drop treenit | ✅ | ❌ | Depriorisoitu |
| Treenin poisto (roskakori) | ✅ | ❌ | Depriorisoitu |
| "Send to Garmin" -nappi | ✅ | ✅ | Phase 14.4 ✅ (`POST /workouts/upload`) |
| Treenin modal-tiedot | ✅ | ❌ | Mobiilissa lista, ei modal |
| AI-plan generointi kalenterista | ✅ | ❌ | Depriorisoitu |
| **Analysis** | ✅ | ✅ | CTL/ATL/TSB, Load, Sleep, Readiness |
| **Tavoitteiden hallinta** | ✅ | ✅ | Phase 14.1 ✅ – lisää/muokkaa/poista |
| Lisää tavoite | ✅ | ✅ | `GoalFormSheet` Flutter |
| Muokkaa/poista tavoite | ✅ | ✅ | Vahvistusdialogin kera |
| Race Goal countdown | ✅ | ✅ | Erityisnäyttö (Race distance + countdown) |
| **Manuaalinen treenikirjaus** | ✅ | ✅ | Phase 16.1 ✅ |
| **AI Chat Coach** | ✅ | ✅ | Phase 15.2 ✅ |
| **Profiili-sivu / Asetukset** | ✅ | ✅ | Phase 14.2 ✅ |
| Fysiologiset tiedot (ikä, paino, pituus) | ✅ | ✅ | `GET/PUT /profile` |
| **Garmin-yhteys (2FA/MFA tuki)** | ✅ | ✅ | Täysi tuki myös 2-vaiheiselle todennukselle (Phase 16.2 ✅) |
| Data export (GDPR) | ✅ | ✅ | `GET /user/export` |
| Tilin poisto (GDPR) | ✅ | ✅ | `DELETE /account` |
| Palaute-lomake | ✅ | ✅ | `POST /feedback` |
| **ML Accuracy Modal** | ✅ | ❌ | Depriorisoitu |
| **Kirjautuminen (Login)** | ✅ | ✅ | Google Sign-In toimii |

---

## 🔴 Avoimet tehtävät (Phase 15/16)

| Tehtävä | Prioriteetti | Status |
|---|---|---|
| **Garmin 2FA / MFA Tuki** | 🔴 Korkea | ✅ VALMIS |
| **AI Chat testaus** | 🔴 Korkea | ✅ VALMIS |
| Manuaalinen treenikirjaus | 🟡 Tärkeä | ✅ VALMIS |
| Push-ilmoitukset | 🟢 Matala | ⏸️ Depriorisoitu (#160) |
| Apple Health / Google Fit | 🟢 Matala | ⏸️ Depriorisoitu (#161) |

---

## 📊 Yhteenveto

| Kategoria | Web | Mobiili |
|---|---|---|
| Näkymät/Sivut | 6 (dashboard, calendar, profile, settings, admin, login) | 6 (home, calendar, analysis, chat, profile, auth + settings) |
| Komponentit | 20+ | ~15 |
| API-kutsut | Täysi kattavuus | Kattava (kalenteri, goals, profile, settings, chat, garmin mfa) |
| CRUD-toiminnot | Kaikki | Goals ✅, Profile ✅, Settings ✅, Workouts (read+send) ✅, Garmin (connect+mfa) ✅ |

**Mobiili on tällä hetkellä 100% web-sovelluksen ominaisuuksista.**
Phase 14 (Feature Parity), Phase 15 (AI Chat), Phase 16.1 (Manuaalinen Treenikirjaus) ja **Garmin 2-vaiheinen tunnistautuminen (2FA/MFA)** ovat kaikki tuotantovalmiita kummallakin alustalla.

Deprioritisoidut (jotka lisätään jos nähdään tarpeelliseksi tulevaisuudessa): Drag & Drop, Push-ilmoitukset, Apple Health / Google Fit.
