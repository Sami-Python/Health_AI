# iOS Migration Plan (Flutter)

Tämä dokumentti sisältää suunnitelman ja vaatimukset The Personal AI Coach -sovelluksen käännökselle ja julkaisulle Applen iOS -käyttöjärjestelmälle. 
Sovelluksen lähdekoodi (Dart) on jo ristiinyhteensopiva (cross-platform), joten itse koodaamista ei tarvitse juurikaan tehdä. Työmäärä muodostuu täysin infrasta ja ekosysteemin sertifikaattien hallinnasta.

## Pakolliset Esivaatimukset

> **Tätä projektia ei pitäisi aloittaa ennen kuin seuraavat asiat ovat kunnossa.**

1. **Apple Developer Program ($99/vuosi)** 
   - Vaaditaan, jotta sovelluksen voi ylipäätään rakentaa ja allekirjoittaa asennettavaan `.ipa` -muotoon pilvessä. 
   - TestFlight (Applen testausjakeluverkko) vaatii myös maksullisen tilin ohjaamista varten.
2. **Apple asetusavaimet (App Store Connect API Keys)** 
   - Joudut luomaan Applen portaalissa avaimet, jotka sijoitetaan GitHub Actionsin `Secrets` -osioon, jotta automatiikka voi allekirjoittaa koodin puolestasi. Koska kehitämme sovellusta Windowsilla ruudun tällä puolella, Mac-pilvikone (CI) tekee taustatyön luvillasi.

## Tekninen Suunnitelma (2-4 tunnin työmäärä)

### 1. Firebase & Google Sign-In Konfiguraatio
- Uudelle iOS Appille on rekisteröitävä paikka Firebasen konsolissa rinnalle Android-versiolle.
- `GoogleService-Info.plist` -tiedoston lataus ja asettaminen polkuun `mobile/ios/Runner/`.
- `ios/Runner/Info.plist` -tiedoston muokkaus Google Sign-In OAuthia varten (lisätään `REVERSED_CLIENT_ID` tauluihin).

### 2. Push-ilmoitukset (Firebase Messaging)
- Koska sovelluksessa on käytössä `firebase_messaging` paketti (vaikkei vielä täydessä käytössä olekaan), iOS-versio vaatii APNs-sertifikaattien (Push Notification `.p8` key) latauksen Applen rekisteristä ja viennin Firebaseen.
- Tausta-ajolupien (Background Fetch & Remote Notifications) aktivointi Xcode / jäsennystiedostoissa.

### 3. CI/CD Putken Rakentaminen Windows-kehittäjille
- Rakennetaan GitHub Actionsiin uusi rutiini: `.github/workflows/mobile-ios-beta.yml`.
- Se asettaa käyttöön `macos-latest` -pilvikoneen.
- Valmistellaan **Fastlane Match** työkalu privaatin GitHub-repositorion (`certificates-repo` tms.) kanssa synkronoimaan provisioning profiilit automaattisesti lennosta – tämä säästää lukemattomia tunteja sertifikaattien ja varmenteiden säätämisessä.
- Action ohjelmoidaan rakentamaan `.ipa` paketti (`flutter build ipa`) ja puskemaan se lopuksi App Store Connectiin / TestFlightiin asennettavaksi.

## Yhteenveto
- Ohjelmointityö Flutter-koodistossa on nolla tai alle 5%.
- Hallinnollinen työ portaaliklikkailussa muodostaa 95% työnkuvasta.
- Fastlane Match & GitHub Actions mahdollistaa iOS-kehityksen jatkamisen saumattomasti myös Windows-koneella.
