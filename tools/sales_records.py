from db_connect import db_connect

cnx = db_connect()

sales_query = ("SELECT Doc_ID, Doc_Date, Doc_Amount, Order_Status, Charge_Street, "
                "Charge_Street2, Charge_Suburb, Charge_State, Charge_Postcode, "
                "Charge_Country, Ship_Attention, Ship_Trading_Name, Ship_Street, "
                "Ship_Street2, Ship_Suburb, Ship_State, Ship_Postcode, Ship_Country, "
                "Ship_Phone, Sales_Rep, Client_Reference "
                "FROM client_docs_header WHERE (Tran_Type = 'SORD') "
                "AND (Client_ID = 1523) ORDER BY Doc_ID DESC")

curA = cnx.cursor(buffered=True)

curA.execute(sales_query)

print(curA)

for row in curA:
    #print("Doc_ID:", row[0], "\tDoc_Date:", row[1], 
    #    "\tDoc_Amount", row[2], "\tOrder_Status:", row[3])

    record_date = str(row[1])
    reformat_date = f"{record_date[8:]}--{record_date[5:7]}--{record_date[0:4]}"

    print("Original\t", record_date, "\tReformatted\t", reformat_date)
    #print(type(record_date))


    #latestDate = f"{lastRecord[8:]}-{lastRecord[5:7]}-{lastRecord[0:4]}"

curA.close()
cnx.close()

