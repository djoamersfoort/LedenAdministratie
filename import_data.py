#!/usr/bin/env python3

#
#  DJANGO_SETTINGS_MODULE=LedenAdministratie.LedenAdministratie.settings ./import_data.py
#

import MySQLdb
import django
django.setup()
from LedenAdministratie.LedenAdministratie.models import *
from datetime import date
from dateutil import parser


def map_types(member, types):
    type_map = {
        'lid': MemberType.objects.get(slug='member'),
        'begeleider': MemberType.objects.get(slug='begeleider'),
        'aspirant_begeleider': MemberType.objects.get(slug='aspirant'),
        'bestuur': MemberType.objects.get(slug='bestuur'),
        'sponsor': MemberType.objects.get(slug='sponsor'),
        'senior': MemberType.objects.get(slug='senior'),
        'strippenkaart': MemberType.objects.get(slug='strippenkaart')
    }

    for member_type in types.split(','):
        if member_type != '':
            member.types.add(type_map[member_type])

    return member


def main():
    password = input("Password: ")
    db = MySQLdb.connect(host='127.0.0.1', port=3306, user='djo_admin', password=password, db='djo_admin')
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM contact')
    for contact in cursor.fetchall():
        member = Member()


        member.id = contact['id']
        member.first_name = contact['voornaam']
        if contact['tussenvoegsels'] and contact['tussenvoegsels'] != '':
            member.last_name = contact['tussenvoegsels'] + " "  + contact['achternaam']
        else:
            member.last_name = contact['achternaam']
        member.email_address = contact['emailadres']
        if contact['emailadres_ouders']:
            member.email_ouders = contact['emailadres_ouders']
        else:
            member.email_ouders = ''
        if contact['geboortedatum']:
            member.gebdat = contact['geboortedatum']
        else:
            member.gebdat = parser.parse('1970-01-01')
        member.straat = contact['adres']
        member.postcode = contact['postcode']
        member.woonplaats = contact['woonplaats']
        member.telnr = contact['mobielnummer']
        member.telnr_ouders = contact['telefoonnummer']
        if contact['begin_datum']:
            member.aanmeld_datum = contact['begin_datum']
        else:
            member.aanmeld_datum = date.today()
        member.afmeld_datum = contact['eind_datum']
        member.hoe_gevonden = contact['hoe_gevonden']
        member.save()
        member = map_types(member, contact['type'])
        member.save()


if __name__ == '__main__':
    main()
