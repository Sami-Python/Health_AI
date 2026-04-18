# Personal AI Coach: Roadmap V2.0

*Seuraavan sukupolven älykkyys, integraatiot ja laitekokemus.* Tässä roadmapissa määritellään projektin suunta sen jälkeen, kun Phase 16 (perusominaisuuksien tasapäistäminen webin ja mobiilin välillä) on suoritettu. Tavoitteena on muuttaa sovellus reagoivasta työkalusta aidosti **proaktiiviseksi ja kokonaisvaltaiseksi tekoälyvalmentajaksi**.

> **Viimeisin valmistunut:** [x] **Phase 36 – Garmin Cloudflare Bypass (Universal Fix v4)** ✅ *(Huhtikuu 2026)*  
> Ratkaistu täysin 403/429-virheet ottamalla käyttöön suora Android SSO -yhteys `curl_cffi`:llä `/portal/api/login`-rajapintaan `GCM_ANDROID_DARK`-jalanjäljellä. Mobiilin HTTP-timeout nostettu 60 sekuntiin Garmin-kirjautumisten ja Gemini AI -vastausten odottamista varten.

---

## Phase 17: Proaktiivinen AI & Automatisoitu Ohjaus (Proactive AI)
## Phase 17: Proaktiivinen AI & Automatisoitu Ohjaus (Proactive AI)
Tekoäly ottaa ohjat omiin käsiin ja ilmoittaa käyttäjälle olennaisista asioista, ennen kuin käyttäjä ehtii edes avata sovelluksen. (Pääosin VALMIS)

- [x] **Morning Briefing (Aamubriefinki):** Tekoäly generoi ja lähettää aamuisin käyttäjän puhelimeen FCM Push-ilmoituksena lyhyen päivän ohjeistuksen perustuen unen määrään, HRV:hen ja suunniteltuun treeniin. (Cloud Scheduler -ohjattu).
- [x] **Weekly Summary (Voikkoyhteenveto):** Automaattisesti päivittyvä, vahvasti välimuistiin paketoitu sanallinen analyysi edellisestä 7 päivästä Dashboardin pääsivulla.
- [ ] **Dynamic Re-scheduling:** Jos käyttäjä skippaa treenin, AI ehdottaa automaattisesti push-ilmoituksella uutta ajankohtaa sen sijaan, että odottaisi kalenterin päivitystä.

---

## Phase 18: Ekosysteemin laajentaminen (Platform Agnostic)
Monipuolistetaan datalähteitä ja vapautetaan sovellus yksinomaan Garmin-ekosysteemistä, jotta kaikki mittarit voidaan yhdistää yhteen näkymään (Bring Your Own Device).

- [ ] **Apple Health / HealthKit -integraatio:** Mahdollisuus lukea askeleet, aktiivisuus ja leposyke iOS-käyttäjiltä ilman Garminia.
- [ ] **Google Fit / Health Connect -integraatio:** Vastaava Android-käyttäjille, tukee WearOS-kelloja ja jopa Withings/Samsung/Polar-laitteita.
- [ ] **Oura Ring / Whoop API -integraatio:** Edistyneet unen ja sykevälivaihtelun (HRV) lukemat erikoislaitteista suoraan AI:n käyttöön.
- [ ] *(Tutkittavaksi: Konenäöllinen ravintoseuranta - Kuva ateriasta -> Gemini AI -> Makrot + treenikuormituksen sovittaminen)*

---

## Phase 19: Laitteisto ja Minisovellukset (Wearable Mini-apps)
Tuodaan valmennuslaitteisto sinne, missä urheilijat katsovat sitä – suoraan ranteeseen treenin aikana.

- [ ] **Garmin Connect IQ Widget/Data Field:** Sovellus kelloon, joka vilkuttaa dynaamisesti värejä tekoälyn reaaliaikaisen analyysin perusteella. (Esim. sininen = lisää vauhtia, punainen = höllää tahtia).
- [ ] **Apple Watch (watchOS) tuki:** Flutterin avulla tehtävä "Sami's AI Coach" kellosovellus iOS-käyttäjille, joka näyttää proaktiivisen treenitilan ja aamubriefingit suoraan kellossa.

---

## Phase 20: Sosiaalisuus & Pelillistäminen (Gamification & Social Teams)
Sovellus on tähän asti ollut yksilösuoritus. Yhteisö sitouttaa yli rajojen.

- [ ] **Valmennusryhmät / Virtuaalitiimit (Leaderboards):** Käyttäjät voivat perustaa ryhmiä. AI Coach analysoi ryhmän kokonaiskuormitusta ja ehdottaa yhteistreenejä tai joukkuetavoitteita.
- [x] **Consistency Score (Johdonmukaisuuspisteet) ✅:** Mitataan 14 päivän liukuvaa keskiarvoa Execution Scoreista ja ylläpidetään "Treeniputkea" (Streak).
- [x] **Badge-järjestelmä ✅:** Tekoäly ojentaa pronssi/hopea/kulta/liekki-tason virtuaalisia pinssejä.

---

## Phase 21: Kehittyneet Ennustemallit & Paikallinen AI (Advanced Modeling)
Rikastetaan koneoppimisanalytiikkaa viemällä sitä yksilöidympiin ennusteisiin terveyden eri aspekteissa.

- [ ] **Riskianalyysi ja Loukkaantumisennusteet:** XGBoost-mallia päivitetään havaitsemaan poikkeavuuksia harjoituskuormituksesta verrattuna palautumisen tasoon (Acute-To-Chronic Workload Ratio + uni). AI antaa konkreettisen prosentuaalisen vammariskin ja hidastaa ohjelmaa aktiivisesti.
- [ ] **Uudet algoritmit:** Muistilla varustetut mallit (esim. LSTM-verkko), joka ymmärtää pitempiä trendejä, kuten ylikunnon kehittyminen viikkojen kuluessa.
- [ ] **Fysiologisen Syklin Seuranta:** Esim. naisten kuukautiskierron seuranta ja sen yhdistäminen AI-valmentajan suosituksiin (esim. kevennys luteaalivaiheen aikana ihon lämpötilan ja palautumisen muutosten perustella).
- [ ] **Offline ML Models (On-device AI):** Treenidatan analytiikka puhelimen NPU (Neural Processing Unit) kautta lennosta, turvaten datayksityisyyttä tehokkaammin.

---

## Phase 22: App Store Release & Tuotteistaminen (Mobile)
Mobiilisovelluksen paketoiminen ja vieminen Google Playhin sekä Apple App Storeen täyttäen molempien alustojen tuotantovaatimukset.

- [x] **Brändäys ja Visuaalisuus ✅:** Kustomoidut sovelluskuvakkeet (App Icon), käynnistysruudut (Splash Screen), ja sovelluksen lopullisen nimen sekä kuvauksen asetus (`pubspec.yaml`).
- [x] **Tuotantoympäristön Konfiguraatiot ✅:** Tuotannon API URLien määritys (esim. flavorien, .envin tai CI/CD -muuttujien avulla) sekä iOS-version Firebase-rekisteröinti (`GoogleService-Info.plist`).
- [x] **Tietoturva & Juridiikka ✅:** Julkaisun (Release/Signing) avainten luonti ja integrointi konfiguraatioon (Android Keystore).
- [x] **Sideloading (Suorajakelu) ✅:** APK-tiedoston kokoaminen ja lisääminen landing pagelle suoraan asennettavaksi ilman sovelluskauppaa.
- [ ] **Kauppojen Vaatimat Materiaalit:** Sovelluskauppoihin edustavat kuvakaappaukset eri laitekokojen (puhelimet ja tabletit) resoluutioilla ja houkuttelevat promootiotekstit. (Vielä tekemättä)

---

## Nice to Have (Tulevaisuuden Visio)
- [ ] **Aamubriefing (Push-ilmoitukset):** Päivittäinen älykäs aamupusku. *(Tehdään myöhemmin)* *Esimerkki: "Huomenta! Body Batterysi on alhainen (32). Ehdotan, että perumme tänään ohjelmassa olevan vetotreenin ja teemme palauttavan 30 min kävelyn. Vahvistatko?"*
- [ ] **Reaaliaikainen Voice-ohjaus (Voice AI):** Mahdollisuus kommunikoida AI-valmentajalle äänellä treenin aikana. *Esimerkki: "Kävelen tänään mieluummin hieman kovempaa – kuinka nopeasti minun tulisi mennä, jotta pysyn peruskestävyysalueella?"*
