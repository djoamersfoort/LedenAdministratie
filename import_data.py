#!/usr/bin/env python3

#
#  DJANGO_SETTINGS_MODULE=LedenAdministratie.LedenAdministratie.settings ./import_data.py
#

import MySQLdb
import django
django.setup()
from LedenAdministratie.LedenAdministratie.models import *


def convert_pw_hash(old_hash):
    new_hash = old_hash.replace('pwh$', 'bcrypt$$')
    return new_hash


def main():
    password = input("Password: ")
    db = MySQLdb.connect(host='127.0.0.1', port=3306, user='idp_prod', password=password, db='idp_main', charset='utf8')
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    query = """
        SELECT userID, backendID, mail, password
        FROM Users
    """

    cursor.execute(query)
    for idp_user in cursor.fetchall():
        print(idp_user)
        try:
            user = User.objects.get(pk=idp_user['userID'])
            print("Updating existing user...")
        except User.DoesNotExist:
            user = User()
            print("Creating new user...")
        user.pk = idp_user['userID']
        user.username = idp_user['mail'].strip()
        user.email = idp_user['mail'].strip()
        user.password = convert_pw_hash(idp_user['password'])
        user.save()

        member_id = idp_user['backendID'].replace('u-', '')
        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            print(f"Member for user not found!")
            continue
        user.first_name = member.first_name
        user.last_name = member.last_name
        user.save()
        member.user = user
        member.save()

    cursor.close()


if __name__ == '__main__':
    main()
