from __future__ import print_function
from db_connect import db_connect
from werkzeug.security import generate_password_hash


cnx = db_connect()

# Get two buffered cursors
curA = cnx.cursor(buffered=True)
curB = cnx.cursor(buffered=True)
 

# Query DB
query_user = ("SELECT UID, UserName, Email FROM users")

add_user = ("INSERT INTO users (UID, UserName, Email, Password) "
            "VALUES (%(uid)s, %(user_name)s, %(email)s, %(password)s)")

curA.execute(query_user)

new_user = {
    'uid': 0,
    'user_name': input("Enter Username: "),
    'email': input("Enter Email: "),
    'password': generate_password_hash(input('Enter password: '), "sha256", salt_length=8)
}

for uid, name, email in curA:
    print(uid, ' ' + name + ' ' + email)
    if name == new_user['user_name']:
        print("Username already in use")
        #return(1)
    elif email == new_user['email']:
        print("Email already in use")
        #return(2)
    if uid > new_user['uid']:
        new_user['uid'] = uid

# Increment new uid by 1
new_user['uid'] += 1

curB.execute(add_user, new_user)

# Close cursor and connection
cnx.commit()
curA.close()
curB.close()

cnx.close()