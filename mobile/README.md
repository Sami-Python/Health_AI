# Health AI Mobile 📱

Mobiilisovellus Health AI -palvelulle. Rakennettu Flutterilla.

## Ominaisuudet
- **Dashboard:** Päivän tärkeimmät metriikat (Readiness, Sleep, Stress).
- **Authentication:** Kirjautuminen (Email/Password, Google Sign-In).
- **Charts:** Visuaaliset kuvaajat palautumiselle ja unelle (Glassmorphism & Gradients).
- **Goals:** Tavoitteiden seuranta.

## Teknologiat
- **Flutter & Dart**
- **State Management:** `setState` & `FutureBuilder` (MVP)
- **Backend:** Python FastAPI (sama kuin webissä)
- **Auth:** Firebase Authentication
- **Http:** `http` package with Auth Interceptor

## Käynnistys

Varmista, että backend on käynnissä (`docker-compose up`).

```bash
# Asenna riippuvuudet
flutter pub get

# Käynnistä (valitse laite)
flutter run
```
