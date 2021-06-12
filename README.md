![Docker](https://github.com/djoamersfoort/LedenAdministratie/workflows/Docker/badge.svg)

# DJO LedenAdministratie
Dit is de source voor de DJO Ledenadminstratie. Geschreven in Python/Django. Features:

## Features
- Leden informatie opslaan en bewerken, inclusief een foto en auto-generated thumbnail
- Facturen aanmaken in PDF formaat (Aanpasbaar HTML/CSS template)
- Facturen automatisch versturen via e-mail, reminders versturen
- (Deel)betalingen van facturen bijhouden
- Notities per lid, met auteur, datum en tijd
- Todo lijst (notitie kan als TODO worden aangemerkt)
- API voor DJO IDP en het Smoelenboek
- Versturen van e-mail met HTML opmaak vanuit de leden-administratie
- Ingebouwde OAuth2 server en user/password management

## Smoelenboek API
Via de smoelenboek API kun je een lijst opvragen met de volgende gegevens:
- Voornaam + Achternaam
- Dag aanwezig
- Thumbnail in embedded JPG of PNG formaat

Om te authenticeren moet je een geldig DJO IDP Access Token in een 'Authorization' header meesturen. Zie verderop voor hoe je an zo'n token komt. Een aantal voorbeelden:

```
curl https://<ledensite>/api/v1/smoelenboek/ -H 'Authorization: Bearer fosjfweijfadojfeiojfaioejeijfeidojf'
```
Dit geeft:

```json
"vrijdag": [
  {
    "id": "<member id>",
    "first_name": "<voornaam>",
    "last_name": "<achternaam>",
    "types": "begeleider,bestuur",
    "photo": "data:image/jpg:base64,<thumbnail base64 encoded>"
  },
  {
    "enzovoorts..."
  }
],
"zaterdag": [
  {
    "id": "<member id>",
    "first_name": "<voornaam>",
    "last_name": "<achternaam>",
    "types": "member",
    "photo": "data:image/jpg:base64,<thumbnail base64 encoded>"
  }
]
```

Je krijgt dus per dag een array van leden terug. Je kunt ook 1 specifieke dag opvragen:

```
curl https://<ledensite>/api/v1/smoelenboek/vrijdag/ -H 'Authorization: IDP fosjfweijfadojfeiojfaioejeijfeidojf'
```
Je krijgt dan dezelfde output als hierboven, alleen zal in dit geval de zaterdag array leeg zijn ("zaterdag": [])

### Smoelenboek details van 1 lid opvragen
Als je alleen de foto van 1 gebruiker wilt opvragen, kan dat als volgt:

```
curl https://<ledensite>/api/v1/smoelenboek/<userid>/ -H 'Authorization: Bearer fosjfweijfadojfeiojfaioejeijfeidojf'
```

Je krijgt dan 1 json hash terug met de details van die user:

```json
  {
    "id": "<member id>",
    "first_name": "<voornaam>",
    "last_name": "<achternaam>",
    "types": "begeleider,bestuur",
    "photo": "data:image/jpg:base64,<thumbnail base64 encoded>"
  }
```

## Docker
Van dit project wordt automatisch een docker container gebouwd. Deze is hier te vinden:

https://github.com/djoamersfoort/LedenAdministratie/packages

Om de image te downloaden kun je dit doen:
docker pull docker.pkg.github.com/djoamersfoort/ledenadministratie/ledenadministratie:latest
Je moet dan wel eerst 'docker login' doen met je github username en een personal access token met packages:read scope.

## OAuth2 server
De ledenadministratie bevat een ingebouwde OAuth2 server, voor het centraal authenticeren van gebruikers in andere applicaties. De gegevens voor het gebruik van deze server zijn als volgt:

### Endpoint URL's
- Authorization Endpoint: https://leden.djoamersfoort.nl/o/authorize/
- Token endpoint: https://leden.djoamersfoort.nl/o/token/

Met een access_token kun je vervolgens de user information API aanroepen:

User info Endpoint: https://leden.djoamersfoort.nl/api/v1/member/details

Deze laatste geeft, afhankelijk van de scopes waarvoor je geautoriseerd bent, de informatie van de ingelogde gebruiker terug in JSON formaat.

### User information API
Voorbeeld response:
```json
{
    "id": "111",
    "firstName": "Henk",
    "middleName": "",
    "lastName": "Jansen",
    "fullName": "Henk Jansen",
    "username": "henk@hier.nl",
    "email": "henk@hier.nl",
    "emailParents": "hetty@daar.nl",
    "dateOfBirth": "2020-06-01",
    "address": "Kerklaan 1",
    "zip": "1234 XX",
    "city": "Amsterdam",
    "phone": "0611111111",
    "memberStatus": true,
    "accountType": "begeleider,lid",
    "backendID": "456"
}
```

Let op: je krijgt alleen de velden die je via de OAUth scopes hebt aangevraagd terug. Zie hieronder voor een lijst met scopes die je kunt aanvragen.

### OAUth scopes
Om de hoeveelheid gedeelde data zo veel mogelijk te beperken, moet een client applicatie 'scopes' aanvragen voor de diverse velden van de user API. De volgende scopes zijn mogelijk:

    'user/basic': 'Je gebruikersnaam en gebruikers-id',
    'user/email': 'Je e-mail adres',
    'user/email-parents': 'Het e-mail adres van je ouders',
    'user/date-of-birth': 'Je geboortedatum',
    'user/address': 'Je adresgegevens',
    'user/telephone': 'Je telefoonnummers',
    'user/names': 'Je voornaam, achternaam en tussenvoegsels',

### OAuth clients registreren
Elke gebruiker kan zelf OAuth clients registeren. Dat gaat als volgt:

1. Log in via https://leden.djoamersfoort.nl/
2. Je komt nu op je profiel pagina. Kies in het linker menu voor 'OAuth applicaties'
3. Je ziet nu een lijst van jouw applicaties, en een knop om er 1 toe te voegen.
4. Klik toevoegen en vul de diverse velden in. Gebruik de client id en client secret in je applicatie oauth client om gebruikers in te loggen via DJO.
