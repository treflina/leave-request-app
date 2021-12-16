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
    "EMAIL_PORT": ""
}



One way of configuration with nginx, gunicorn, supervisor is to create eg. gunicorn_start file in virtual environment bin (project files are located inside virtual environment folder):

#!/bin/bash

NAME="wnioski"                                  # Name of the application
DJANGODIR=/directory/virtualenv/wnioski             # Django project directory
SOCKFILE=/directory/virtualenv/run/gunicorn.sock  # we will communicte using this unix socket
USER=root                                        # the user to run as (it's not recommandable to leave it as root)
GROUP=root                                     # the group to run as (it's not recommandable to leave it as root)
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
  
  
  
  

NGINX CONFIGURATION (example with webapps as directory, wnioskivenv as project virtual environment)

upstream wnioski_server {
  server unix:/webapps/wnioskivenv/run/gunicorn.sock fail_timeout=0;
}
 
server {
 
    listen   80;
    server_name 46.41.138.161;
 
    access_log /webapps/wnioskivenv/logs/nginx-access.log;
    error_log /webapps/wnioskivenv/logs/nginx-error.log;
 
    location /static/ {
        alias   /webapps/wnioskivenv/wnioski/static/;
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



SUPERVISOR:

[program:wnioski]
command = /webapps/wnioskivenv/bin/gunicorn_start                    ; Command to start app
user = root                                                          ; User to run as
stdout_logfile = /webapps/wnioskivenv/logs/gunicorn_supervisor.log   ; Where to write log messages
redirect_stderr = true                                                ; Save stderr in the same log
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8                       ; Set UTF-8 as default encoding



