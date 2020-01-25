import os
import time

DB_NAME = 'stbot'
# PROXY = {'https': 'socks5://<host>:<port>'}
PROXY = {}
PROJECT_NAME = 'stbot'

HOST = '0.0.0.0'
PORT = 8080
WORKERS = 1

os.environ['TZ'] = 'Europe/Moscow'
time.tzset()  # unix only
