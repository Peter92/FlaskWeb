import random
import os

APP_SECRET_KEY = 'secret key here'

#Remove this line for production
APP_SECRET_KEY = str(random.getrandbits(64))

PRODUCTION_SERVER = False

DATABASE_HOST = 'localhost'

DATABASE_NAME = 'website_test'

DATABASE_USER = 'root'

DATABASE_PASSWORD = 'mg3GaTPhHV0DFwgsVGHT9@ZrW%pUdwAXn9sH5J73WCFlbjvF01cfm1l@dNc4diYM'

BAN_TIME_IP = 300

BAN_TIME_ACCOUNT = 150

MAX_LOGIN_ATTEMPTS_IP = 30

MAX_LOGIN_ATTEMPTS_ACCOUNT = 15

PERMISSION_DEFAULT = 0

PERMISSION_REGISTERED = 10

PERMISSION_ACTIVATED = 20

PERMISSION_TRUSTED = 100

PERMISSION_MODERATOR = 150

PERMISSION_ADMIN = 200

PERMISSION_WEBMASTER = 255

EMAIL_HTML_PERMISSION = PERMISSION_ADMIN

ACCEPT_REQUEST_WITH_NO_HEADERS = False #Should a POST request be blocked if it contains no origin or request headers? Disable if causing issues.

#DATABASE_NAME = 'peter_pythontest'

#DATABASE_USER = 'peter_admin'