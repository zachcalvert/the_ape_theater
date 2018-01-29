from .base import *

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}

SECRET_KEY = 'p4@eqiv)7wqfe*5zfis-&ta#tew75!afnff!%v^9=50%(@5kzb'

DEBUG = True