import os
import requests
import urllib.parse
import mysql.connector


from flask import redirect, render_template, request, session
from functools import wraps
from werkzeug.security import check_password_hash


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def check_password(hashed, password):
    if not check_password_hash(hashed, password):
        return apology("Invalid Password", 403)


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/rotadyne/login")
        return f(*args, **kwargs)
    return decorated_function


def get_status(stat_int):
    switcher = {
        0: "Open",
        1: "Part",
        2: "Full",
        3: "Closed",
        4: "Suspended",
        5: "Cancelled"
    }

    return switcher.get(int(stat_int), "Status Undefined")
    
    # switch case for python 3.10
    """
    match int(stat_int):
        case 0:
            return "Open"
        case 1:
            return "Part"
        case 2:
            return "Full" 
        case 3:
            return "Closed"
        case 4:
            return "Suspended"
        case 5:
            return "Cancelled"
        case _:
            return "Status Undefined"
    """


def db_connect(caller):
    """
    https://dev.mysql.com/doc/connector-python/en/connector-python-option-files.html
    https://dev.mysql.com/doc/refman/8.0/en/option-files.html
    https://dev.mysql.com/doc/refman/8.0/en/mysql-config-editor.html    <- Not working

    """
    if caller == 's':
        return mysql.connector.connect(option_files='/etc/mysql/connectors.cnf', database='so_random')
    # Return mysql connection object
    elif caller == 'r':
        return mysql.connector.connect(option_files='/etc/mysql/connectors.cnf', database='rotadynerds')
    '''
    cnx = mysql.connector.connect(option_files='/etc/mysql/connectors.cnf')
    return cnx
    '''
