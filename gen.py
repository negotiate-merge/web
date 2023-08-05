import requests
import random
from bs4 import BeautifulSoup
from datetime import date
from datetime import timedelta
from helpers import db_connect
from flask import session


def get_date(lastDrawn):
    """Detirmines if the current date is after the date of the last known draw"""
    #last = date.fromisoformat(str(lastDrawn))    # Create date object from string
    last = lastDrawn[0]
    nextDraw = last + timedelta(days=7)         # Calculate date of next draw
    today = date.today()                    # Get todays date
    # print(f"last:    {last}    {type(last)}\ntoday:    {today}    {type(today)}\nnext:    {nextDraw}    {type(nextDraw)}")
    if today >= nextDraw:
        return True
    else:
        return False
        


def aggregate(db, weeks):
    # Respective hot/cold thresholds
    normalMedian = 11 #10
    powerMedian = 3 #3
    
    # Initialize arrays for hot and cold ball trackers
    coldNumbers = []
    hotNumbers = []
    coldPowers = []
    hotPowers = []


    # Count number of times each ball is drawn
    # global numbers
    # global powers
    numbers = {}
    powers = {}
    # Sets counters to 0
    for n in range(1,36):
        if n <= 20:
            numbers[str(n)] = 0
            powers[str(n)] = 0
        else:
            numbers[str(n)] = 0

    # Get past years draws for current heat
    years_query = ("SELECT numbers, powerball FROM results ORDER BY drawDate DESC LIMIT %s")
    db.execute(years_query, (weeks,))

    # Delete first record (most recent result) for the previous weeks results
    # if (weeks == 53):
    #     del(db[0]) #del(pool[0]) 
    w = weeks
    # Count ball draw occurances
    while w:
        if w == 53:
            #print(f"w is {w} skipping first")
            row = db.fetchone()
            # print(row)
            w -= 1
            pass
        # print(f"w is {w}")
        row = db.fetchone()

        nums = row[0].split(',')
        power = row[1]
        # print(f"nums is {nums} power is {power}")
        w -= 1
        for n in nums:
            if n in numbers:
                numbers[n] = numbers[n] + 1
        if power in powers:
            powers[power] = powers[power] + 1


    # Divide balls into hot and cold arrays
    # Normal balls
    for value in numbers:
        if numbers[value] > normalMedian - 1:
            if value not in hotNumbers:
                hotNumbers.append(value)
        elif value not in coldNumbers:
            coldNumbers.append(value)
        
    # Power balls
    for value in powers:
        if powers[value] > powerMedian - 1:
            if value not in hotPowers:
                hotPowers.append(value)
        elif value not in coldPowers:
            coldPowers.append(value)

    # Return collection of aggregates
    aggregates = {}
    aggregates['coldNumbers'] = coldNumbers
    aggregates['hotNumbers'] = hotNumbers
    aggregates['coldPowers'] = coldPowers
    aggregates['hotPowers'] = hotPowers

    # Clears number tracking arrays for use on the next run
    if (weeks == 53):
        coldNumbers = []
        hotNumbers = []
        coldPowers = []
        hotPowers = []

    # Need to store these in session for access accross gunicorn PID's
    session['coldNumbers'] = coldNumbers
    session['hotNumbers'] = hotNumbers
    session['coldPowers'] = coldPowers
    session['hotPowers'] = hotPowers

    # curA.close()
    # cnx.close()

    return aggregates


def dbUpdate(URL):
    """Scrape results and update db"""
    # Check if latest results have already been inserted
    # lastDrawn = db.execute("SELECT MAX(drawDate) AS drawDate FROM results")[0]['drawDate']
    lastDrawn_query = ("SELECT MAX(drawDate) AS drawDate FROM results ORDER BY drawDate DESC")

    # Get buffered cursor
    cnx = db_connect('s')
    curA = cnx.cursor(buffered=True)
    curA.execute(lastDrawn_query)
    lastDrawn = curA.fetchone()
    
    if get_date(lastDrawn):
        print("Udpating database")
        # Get html content, setup BeautifulSoup object
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        
        # Remove ads from results table
        for ad in soup.find_all("tr", {'class':'noBox'}): 
            ad.decompose()
        
        # Find element by html id tag, get all tr elements & delete table header
        results = soup.find(id="content")
        draws = results.find_all('tr')
        print(f"draws is of type {type(draws)}")
        # Remove header
        del(draws[0])

        # Insert into db if not present
        date_query = ("SELECT drawDate FROM results")
        curA.execute(date_query)

        listedDates = []
        for _ in curA:
            date = curA.fetchone()
            if date is not None:
                # print(date[0])
                listedDates.append(str(date[0]))
        
        # Parse data from html tags
        # Refactor date for SQL insertion
        rawDate = draws[0].find('a', href=True)['href']
        date = rawDate[19:]
        d = date[0:2]
        m = date[3:5]
        y = date[6:]
        cleanDate = f"{y}-{m}-{d}"
        # print(cleanDate)

        # Extract drawn numbers from soup
        rawNumbers = draws[0].find_all("li", class_="result medium pb ball dark ball")
        powerball = draws[0].find("li", class_="result medium pb ball dark powerball").text
        numbers = []
        
        for number in rawNumbers:
            numbers.append(number.text)
        
        numString = ','.join(numbers)

        print(f"numString:  {numString}\npowerball:  {powerball}\ncleanDate:  {cleanDate}")

        print(f"cleandate has type {type(cleanDate)}")
        print(f"listedDates[0] has type {type(listedDates[0])}")

        if cleanDate not in listedDates:
            #print("need to insert here")
            curB = cnx.cursor(buffered=True)
            insertDraw_query = ("INSERT INTO results (numbers, powerball, drawDate) VALUES (%s, %s, %s)")
            curB.execute(insertDraw_query, (numString, powerball, cleanDate,))
            cnx.commit()
            curB.close()        
    else:
        print("Database up to date")
    
    curA.close()
    cnx.close()


# Draw normal balls based on hotness
def drawBall(code):
    while True:
        n = random.randint(1,35)
        if code == 'h' and n in session['hotNumbers']:
            break
        elif code == 'c' and n in session['coldNumbers']:
            break
        elif code == 'r':
            break
    return n


# Draw power balls based on hotness
def drawPower(code):
    while True:
        n = random.randint(1,20)
        if code == 'h' and n in session['hotPowers']:
            break
        elif code == 'c' and n in session['coldPowers']:
            break
        elif code == 'r':
            break
    #print(f"Power = {n}")
    return n


def changeState():
    # This function changes the array values from str to their int counterpart
    arrays = [session['hotNumbers'], session['coldNumbers'], session['hotPowers'], session['coldPowers']]
    for array in arrays:
        count = 0
        while count != len(array):
            array[count] = int(array[count])
            count += 1


def getLastDraw(db):
    # Get numbers from last draw
    numbers = {}
    db.execute("SELECT numbers, powerball FROM results ORDER BY drawDate DESC LIMIT 1")
    lastDraw = db.fetchone()
    
    #print(f"lastDraw = {lastDraw}")
    nums =  lastDraw[0].split(',')
    numbers['lastNums'] = nums
    numbers['lastPower'] = lastDraw[1]

    return numbers
