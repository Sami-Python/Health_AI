# Tervetuloa Health AI Coach -ohjelmaan

Henkilökohtainen tekoälyavusteinen kestävyysurheiluvalmentajasi.

## Yleiskatsaus

Health AI Coach yhdistää Garmin-laitteiden datan, fysiologiset mittarit (sykevälivaihtelu, uni, stressi) ja koneoppimisen (XGBoost + Google Gemini) tarjotakseen yksilöityjä ja mukautuvia harjoitusohjelmia.

## Pikalinkit

- [Tuotannon Roadmap](production_roadmap.md) – Nykyinen tila ja tulevaisuuden tavoitteet
- [Arkkitehtuuri](arkkitehtuuri.md) – Järjestelmäsuunnittelu ja komponenttien vuorovaikutus
- [API-viitteet](API.md) – Backend API -dokumentaatio
- [Tietoturva-auditointi](security_audit.md) – Tietoturvahavainnot ja tila

## Julkaisu (Deployment)

Tutustu [julkaisuoppaaseen](deployment.md) aloittaaksesi kehitys- tai tuotantoympäristössä.

## Ominaisuudet

- **Mukautuva harjoittelu:** Ohjelmat joustavat päivittäisen palautumisesi mukaan (Body Battery, TSB).
- **AI-valmennus:** Päivittäiset oivallukset ja treenimuokkaukset LLM:n avulla.
- **Garmin Export:** Vie tekoälyn luomat harjoitukset suoraan Garmin-kellon kalenteriin.
- **Kisavalmistautuminen:** Kohdistettu tavoiteseuranta kisoja varten.
- **Tietosuoja:** GDPR-yhteensopivuus ja salatut tunnukset.
