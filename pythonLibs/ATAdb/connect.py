"""
set of scripts to connect to databases
"""

import mysql.connector
import logging
import os
from pathlib import Path
from configparser import ConfigParser


class DBConnectException(Exception):
    pass


def connect_to_db(db_name, credentials_dir=None):
    logger = logging.getLogger(__name__)

    # Find 
    if not credentials_dir:
        credentials_dir = os.environ.get('DB_AUTH_DIR')
    if not credentials_dir:
        raise DBConnectException('No path to credentials specified')

    logging.debug('Credentials path: ' + credentials_dir)
    credentials_path = Path(credentials_dir)
    if not credentials_path.exists():
        raise DBConnectException('Credentials path does not exist - {:s}'.format(credentials_dir))

    auth_file = credentials_path / 'dbauth.cfg'
    if not auth_file.exists():
        raise DBConnectException('Non-existant configuration file \"{:s}\"'.format(auth_file))
    auth_config = ConfigParser()
    try:
        if len(auth_config.read([str(auth_file)], 'utf-8')) != 1:
            raise Exception()
    except:
        raise DBConnectException('Error parsing configuration file {:s}'.format(auth_file))

    # OK, got the configuration for known databases
    # Check if the requested db is configured

    if not auth_config.has_section(db_name):
        raise DBConnectException('Unknown database \"{:s}\"'.format(db_name))
        
    # Got the configuration.  Assemble the connect call
    # bool and cert parameters require special attention.
    
    connect_dict = {}
    for key, value in auth_config[db_name].items():
        if value.lower() in ['false', 'true']:
            value = bool(value)
        elif isinstance(value, str) and value.endswith('.pem'):
            value = str(credentials_path / value)
        connect_dict[key] = value
        
    logging.debug(connect_dict)

    try:
        return mysql.connector.connect(**connect_dict)
    except Exception as e:
        message = 'Connect to {:s} failed: {:s}'.format(db_name, str(e))
#        logger.exception(message)
        raise DBConnectException(message)


if __name__ == "__main__":
    FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT,datefmt='%Y-%m-%d %H:%M:%S')
    db = connect_to_db('ata-ro')
    print('success')
    exit(0)

    cx = db.cursor() 
    query=("select ant,pax_box_sn from feed_parts")
    cx.execute(query)
    records = cx.fetchall() 
    for r in records:
        print(r)
    cx.close()
    db.close()

