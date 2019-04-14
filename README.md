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

## Smoelenboek API
Via de smoelenboek API kun je een lijst opvragen met de volgende gegevens:
- Voornaam + Achternaam
- Dag aanwezig
- Thumbmail in embedded JPG of PNG formaat

Om te authenticeren moet je een geldig DJO IDP Access Token in een 'Authorization' header meesturen. Een aantal voorbeelden:

```
curl https://<ledensite>/api/v1/smoelenboek/ -H 'Authorization: IDP fosjfweijfadojfeiojfaioejeijfeidojf'
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
curl https://<ledensite>/api/v1/smoelenboek/<userid>/ -H 'Authorization: IDP fosjfweijfadojfeiojfaioejeijfeidojf'
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

https://cloud.docker.com/u/djoamersfoort/repository/docker/djoamersfoort/ledenadministratie

Om de image te downloaden kun je dit doen:
docker pull djoamersfoort/ledenadministratie
