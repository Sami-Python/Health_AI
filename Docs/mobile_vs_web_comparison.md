# 📱 Mobile (Flutter) vs Web (Next.js) – Feature Vertailu

> **Päivitetty:** 2026-02-25
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
| \"Send to Garmin\" -nappi | ✅ | ✅ | Phase 14.4 ✅ (`POST /workouts/upload`) |
| Treenin modal-tiedot | ✅ | ❌ | Mobiilissa lista, ei modal |
| AI-plan generointi kalenterista | ✅ | ❌ | Depriorisoitu |
| **Analysis** | ✅ | ✅ | CTL/ATL/TSB, Load, Sleep, Readiness |
| **Tavoitteiden hallinta** | ✅ | ✅ | Phase 14.1 ✅ – lisää/muokkaa/poista |
| Lisää tavoite | ✅ | ✅ | `GoalFormSheet` Flutter |
| Muokkaa/poista tavoite | ✅ | ✅ | Vahvistusdialogin kera |
| Race Goal countdown | ✅ | ✅ | Erityisnäyttö (Race distance + countdown) |
| **Manuaalinen treenikirjaus** | ✅ | ✅ | Phase 16.1 ✅ |
| **AI Chat Coach** | ✅ | ✅ | Phase 15.2 ✅ |
| **Profiili-sivu** | ✅ | ✅ | Phase 14.2 ✅ |
| Fysiologiset tiedot (ikä, paino, pituus) | ✅ | ✅ | `GET/PUT /profile` |
| Garmin-tunnusten hallinta | ✅ | ✅ | Syötä/vaihda/poista |
| **Asetukset (Settings)** | ✅ | ✅ | Phase 14.3 ✅ |
| Data export (GDPR) | ✅ | ✅ | `GET /user/export` |
| Tilin poisto (GDPR) | ✅ | ✅ | `DELETE /account` |
| Palaute-lomake | ✅ | ✅ | `POST /feedback` |
| **ML Accuracy Modal** | ✅ | ❌ | Depriorisoitu |
| **Kirjautuminen (Login)** | ✅ | ✅ | Google Sign-In toimii |

---

## 🔴 Avoimet tehtävät (Phase 15)

| Tehtävä | Prioriteetti | Status |
|---|---|---|
| **AI Chat testaus** – fyysinen puhelin tai emulaattori | 🔴 Korkea | ✅ VALMIS |
| Manuaalinen treenikirjaus | 🟡 Tärkeä | ✅ VALMIS |
| Push-ilmoitukset | 🟢 Matala | ⏸️ Depriorisoitu (#160) |
| Apple Health / Google Fit | 🟢 Matala | ⏸️ Depriorisoitu (#161) |

---

## 📊 Yhteenveto

| Kategoria | Web | Mobiili |
|---|---|---|
| Näkymät/Sivut | 6 (dashboard, calendar, profile, settings, admin, login) | 6 (home, calendar, analysis, chat, profile, auth + settings) |
| Komponentit | 20+ | ~15 |
| API-kutsut | Täysi kattavuus | Kattava (kalenteri, goals, profile, settings, chat) |
| CRUD-toiminnot | Kaikki | Goals ✅, Profile ✅, Settings ✅, Workouts (read+send) ✅ |

**Mobiili on tällä hetkellä ~95% web-sovelluksen ominaisuuksista.**
Phase 14 (Feature Parity), Phase 15 (AI Chat), ja Phase 16.1 (Manuaalinen Treenikirjaus) ovat kaikki tuotantovalmiita ja testattu.

Deprioritisoidut: Drag & Drop kalenteri, ML Accuracy Modal, Push-ilmoitukset, Apple Health / Google Fit.
