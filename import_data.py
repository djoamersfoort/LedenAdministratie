from LedenAdministratie.models import Lid
from dateutil.parser import parse

def fix_phone(nr):
    if nr != '' and not nr.startswith('0'):
        nr = '0' + nr
    nr = ''.join(i for i in nr if ord(i) < 128)
    nr = nr.replace(' ', '')
    return nr

def fix_datum(dt, nullok=True):
    dt = dt.strip()
    if dt == '' and not nullok:
        return parse('01-01-1900')
    elif dt == '':
        return None
    return parse(dt, dayfirst=True)


with open("Ledenlijst.csv", 'r', encoding='iso8859-15') as csv:
    first = True
    for line in csv.readlines():
        if first:
            first = False
            continue
        fields = line.split(';')
        print("Importing: %s" % fields[0])
        lid = Lid()
        geslacht = fields[1].strip('(').strip(')').lower()
        lid.geslacht = geslacht
        lid.first_name = fields[2].strip()
        lid.last_name = fields[3].strip()
        lid.email_address = fields[4].strip()
        print("Datum: " + fields[5].strip())
        lid.gebdat = fix_datum(fields[5].strip(), nullok=False)
        lid.straat = fields[6].strip()
        lid.woonplaats = fields[7].strip().title()
        lid.telnr = fix_phone(fields[8].strip())
        lid.postcode = fields[9].strip()
        lid.scouting_nr = fields[10].strip()
        speltak = fields[11].strip().lower()
        if speltak.lower() == 'stamgroep':
            speltak = 'stam'
        lid.speltak = speltak
        lid.aanmeld_datum = fix_datum(fields[12].strip())
        lid.inschrijf_datum_sn = fix_datum(fields[13].strip())
        lid.mobiel = fix_phone(fields[14].strip())
        lid.tshirt_maat = fields[15].strip()
        lid.verzekerings_nr = fields[16].strip()
        lid.jub_badge = fields[17].strip()
        lid.opmerkingen = fields[18].strip()
        lid.bijzonderheden = fields[19].strip()
        lid.mobiel_ouder1 = fix_phone(fields[20].strip())
        lid.mobiel_ouder2 = fix_phone(fields[21].strip())
        lid.email_ouder1 = fields[22].strip()
        lid.email_ouder2 = fields[23].strip()
        lid.save()
        lid.aanmeld_datum = fix_datum(fields[12].strip())
        lid.save()


# 0    memID;
# 1    Geslacht;
# 2    Voornaam;
# 3    Achternaam;
# 4    Email;
# 5    GebDatum;
# 6    Straat;
# 7    Plaats;
# 8    Telefoon;
# 9    PostC;
# 10    ScoutingNummer;
# 11    Speltak;
# 12    JoinDate;
# 13    InschrijfDatum;
# 14    Mobiel;
# 15    Tshirt;
# 16    Verzekering;
# 17    Jubbadge;
# 18    Opmerkingen;
# 19    Bijzonderheden;
# 20    MobielOuder1;
# 21    MobielOuder2;
# 22    EmailOuder1;
# 23    EmailOuder2;
# 24    Leeftijd
# 25    31 / 12
