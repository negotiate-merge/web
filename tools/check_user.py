from db_connect import db_connect

cnx = db_connect('r')

# Get buffered cursor
curA = cnx.cursor(buffered=True)

print("Check if a username is present in the database")
username = input("Enter username to query: ")

query = ("SELECT UID, Client_ID, UserName, FirstName, Surname FROM users WHERE UserName = %s")

curA.execute(query, (username,))
row = curA.fetchone()

if row == None:
    print(f"{username} not present in databse")
else:
    print(row)

curA.close()
cnx.close()
