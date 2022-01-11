# wnioskimbp
Python 3.6 or later is required. 

Settings are configured to work with MySQL ( installation of mysqlclient driver is needed ).


Place file called secret.json in base directory. The content should look this way:
{
    "FILENAME": "secret.json",
    "SECRET_KEY": "yoursecretkey",
    "DB_NAME": "yourdatabasename",
    "DB_USER": "databaseuser",
    "DB_PASSWORD": "databasepassword",
    "ALLOWED_HOSTS": ["localhost", "127.0.0.1", "other IP adresses"],
    "DEFAULT_FROM_EMAIL": "",
    "EMAIL_HOST": "",
    "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "",
    "EMAIL_PORT": "", 
    "DEBUG": "False",
}
DEBUG MODE should be set to FALSE in production!



SERVER SETUP WITH NGINX, GUNICORN, SUPERVISOR

sudo apt-get update && sudo apt-get upgrade
pip3 install pip --upgrade
(export PYTHONIOENCODING="UTF-8")

sudo apt install git nginx supervisor

mkdir /webapps
cd webapps

sudo apt-get python3-venv
python3 -m venv wnioskivenv

cd wnioskivenv
git clone https://github.com/../wnioski

source bin/activate

cd wnioski 
python3 install -r requirements.txt
pip freeze --local 
python3 install gunicorn

cd ..
cd bin 
touch gunicorn_start

GUNICORN_START

#!/bin/bash

NAME="wnioski"                                  # Name of the application
DJANGODIR=/webapps/wnioskivenv/wnioski             # Django project directory
SOCKFILE=/webapps/wnioskivenv/run/gunicorn.sock  # we will communicte using this unix socket
USER=root                                        # the user to run as (it's not recommandable to have root as user)
GROUP=root                                     # the group to run as (it's not recommandable to have root as user)
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=wnioski.settings             # which settings file should Django use
DJANGO_WSGI_MODULE=wnioski.wsgi                     # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source ../bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ../bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-



chmod u+x gunicorn_start #add permissions 
gunicorn_start  #check if it works

SUPERVISOR

cd /etc/supervisor/conf.d/
touch wnioski.conf 

[program:wnioski]
command = /webapps/wnioskivenv/bin/gunicorn_start                    ; Command to start app
user = root                                                          ; User to run as
stdout_logfile = /webapps/wnioskivenv/logs/gunicorn_supervisor.log   ; Where to write log messages
redirect_stderr = true                                                ; Save stderr in the same log
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8                       ; Set UTF-8 as default encoding

cd /webapps/wnioskivenv
mkdir logs
touch logs/gunicorn_supervisor.log

supervisorctl reread  #wnioski:available (correct response)
supervisorctl update # wnioski: added process group


NGINX

cd /etc/nginx/sites-available/
touch wnioski

upstream wnioski_server {
  server unix:/webapps/wnioskivenv/run/gunicorn.sock fail_timeout=0;
}
 
server {
 
    listen   80;
    server_name 46.41.138.161;
 
    access_log /webapps/wnioskivenv/logs/nginx-access.log;
    error_log /webapps/wnioskivenv/logs/nginx-error.log;
 
    location /static/ {
        alias   /webapps/wnioskivenv/wnioski/staticfiles/;
    }
    
    location /media/ {
        alias   /webapps/wnioskivenv/wnioski/media/;
    }
 
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;

        if (!-f $request_filename) {
            proxy_pass http://wnioski_server;
            break;
        }
    }
}

cd 
ln -s /etc/nginx/sites-available/wnioski /etc/nginx/sites-enabled/wnioski

service nginx restart
supervisorctl restart wnioski #to check

cd webapps/wnioskivenv/logs
touch nginx-access.log
touch nginx-error.log

cd ..
cd wnioski
python manage.py collectstatic             #to create staticfiles - STATIC_ROOT in settings
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

