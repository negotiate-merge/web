import mysql.connector

def db_connect(caller):
    """
    https://dev.mysql.com/doc/connector-python/en/connector-python-option-files.html
    https://dev.mysql.com/doc/refman/8.0/en/option-files.html
    https://dev.mysql.com/doc/refman/8.0/en/mysql-config-editor.html    <- Not working

    """
    # Return mysql connection object
    if caller == 'r':
        return mysql.connector.connect(option_files='/etc/mysql/connectors.cnf', database='rotadynerds')
    '''
    cnx = mysql.connector.connect(option_files='/etc/mysql/connectors.cnf')
    return cnx
    '''