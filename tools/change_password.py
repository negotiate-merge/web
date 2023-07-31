from db_connect import db_connect
from werkzeug.security import check_password_hash, generate_password_hash

cnx = db_connect('r')

curA = cnx.cursor(buffered=True)
curB = cnx.cursor(buffered=True)

# Stored Querys
get_passwords = ("SELECT UID, Password, Password2 FROM users WHERE UserName = %s")

update_password = ("UPDATE users SET Password = %s, Password2 = %s, Password3 = %s "
                    "WHERE UID = %s")

# Get username and confirm validity
username = input("Enter username for password change: ")

curB.execute(get_passwords, (username,))
row = curB.fetchone()

if row is not None:
    phrase = input("Enter password: ")
    password = generate_password_hash(phrase, "sha256", salt_length=8)

    # User struct
    user = {
        'uid': row[0],
        'p1': password,
        'p2': row[1],
        'p3': row[2]
    }

    curA.execute(update_password, (user['p1'], user['p2'], user['p3'], user['uid']))
    #print(user)
else:
    print("Invalid user")

cnx.commit()
curA.close()
curB.close()
cnx.close()