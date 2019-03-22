#!/usr/bin/env python3

#
#  DJANGO_SETTINGS_MODULE=LedenAdministratie.LedenAdministratie.settings ./import_data.py
#

import MySQLdb
import django
django.setup()
from LedenAdministratie.LedenAdministratie.models import *
from datetime import date, datetime
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
    db = MySQLdb.connect(host='127.0.0.1', port=3306, user='djo_admin', password=password, db='djo_admin', charset='utf8')
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    query = """
        SELECT *, dagdeel.dag FROM contact
        INNER JOIN contact_dagdeel cd
        INNER JOIN dagdeel
        ON (cd.contact_id = contact.id AND cd.dagdeel_id = dagdeel.id)
        WHERE contact.eind_datum IS NULL
        AND dagdeel.eind_datum IS NULL
    """

    cursor.execute(query)
    for contact in cursor.fetchall():
        print(contact)
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
        if contact['dagdeel.dag'] == 'vr':
            member.dag_vrijdag = True
        if contact['dagdeel.dag'] == 'za':
            member.dag_zaterdag = True

        try:
            with open("export/images/contacten/{0}.jpg".format(member.id), "rb") as f:
                member.foto = f.read()
        except:
            print("Warning: no photo found for id {0}".format(member.id))

        member.save()
        member = map_types(member, contact['type'])
        member.save()

    # Import notes
    cursor.execute("SELECT * FROM notitie")
    for note in cursor.fetchall():
        try:
            member = Member.objects.get(id=note['contact_id'])
        except Member.DoesNotExist:
            continue
        print(note)
        newnote = Note()
        newnote.id = note['id']
        newnote.member = member
        newnote.text = note['tekst']
        newnote.created = datetime.fromtimestamp(int(note['datum_tijd']))
        newnote.username = 'Importer'
        newnote.done = (note['toekomst'] == '0')
        newnote.save()
        newnote.created = datetime.fromtimestamp(int(note['datum_tijd']))
        newnote.save()

    # Imort invoices
    cursor.execute("SELECT * FROM factuur")
    for invoice in cursor.fetchall():
        try:
            member = Member.objects.get(id=invoice['contact_id'])
        except Member.DoesNotExist:
            continue
        print(invoice)
        newinvoice = Invoice()
        newinvoice.id = invoice['id']
        newinvoice.member = member
        newinvoice.username = 'Importer'
        newinvoice.amount = invoice['bedrag']
        if invoice['betaald'] == '1':
            newinvoice.amount_payed = newinvoice.amount
            newinvoice.sent = newinvoice.created
        newinvoice.created = invoice['datum']
        newinvoice.save()

        try:
            with open("export/facturen/{0}.pdf".format(newinvoice.old_invoice_number), "rb") as f:
                newinvoice.pdf = f.read()
        except:
            print("Warning: no invoice PDF found: export/facturen/{0}.pdf".format(newinvoice.old_invoice_number))

        newinvoice.created = invoice['datum']
        newinvoice.save()


if __name__ == '__main__':
    main()
