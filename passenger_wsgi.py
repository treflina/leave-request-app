import os
import sys
from urllib.parse import unquote

from django.core.wsgi import get_wsgi_application

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = "wnioski.settings"

def application(environ, start_response):
    environ["PATH_INFO"] = unquote(environ["PATH_INFO"]).encode('utf-8').decode('iso-8859-1')
    _application = get_wsgi_application()
    return _application(environ, start_response)