# Electronic requests approval workflow with other features (WebApp)

This app enables an electronic requests approval workflow.
Other main functions:

- information about the amount of time off left
- employee listing for a manager that gives details like eg. a contract end date, a possibility to quickly check if an empoyee should be present at work today
- e-mail notifications to a manager that a request's been sent
- pdf report generator about days off, sick leaves
- sick leaves registration page
- possibility to download documents (like regulations, private insurance contract rules etc.) for employees

Written in Python with Django 3.2. Responsive (including tables).

Python 3.6 or later is required.
Settings are configured to work with MySQL database ( installation of mysqlclient driver is needed ).

## Configuration on Ubuntu 18.04 server with NGINX, Gunicorn & Supervisor

```
sudo apt-get update && sudo apt-get upgrade
pip3 install pip --upgrade
sudo apt install git nginx supervisor

export PYTHONIOENCODING="UTF-8"
```

## Create folders, virtual environment and copy the source code

```
mkdir /webapps
cd webapps

sudo apt-get python3-venv
python3 -m venv wnioskivenv

cd wnioskivenv
git clone https://github.com/treflina/wnioski.git

source bin/activate

cd wnioski
pip3 install -r requirements.txt
sudo apt-get install gettext
sudo apt-get install libmagic1
```

In case there's a problem with installing Pillow:

```
apt install libjpeg8-dev zlib1g-dev libtiff-dev libfreetype6 libfreetype6-dev libwebp-dev libopenjp2-7-dev libopenjp2-7-dev -y

pip3 install pillow --global-option="build_ext" --global-option="--enable-zlib" --global-option="--enable-jpeg" --global-option="--enable-tiff" --global-option="--enable-freetype" --global-option="--enable-webp" --global-option="--enable-webpmux" --global-option="--enable-jpeg2000"
```

Place a file called secret.json in this base directory. The content should look this way:

```
{
    "FILENAME": "secret.json",
    "SECRET_KEY": "yoursecretkey",
    "DB_NAME": "yourdatabasename",
    "DB_USER": "databaseuser",
    "DB_PASSWORD": "databasepassword",
    "ALLOWED_HOSTS": ["localhost", "127.0.0.1", "other IP adresses", "domain"],
    "DEFAULT_FROM_EMAIL": "",
    "EMAIL_HOST": "",
    "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "",
    "EMAIL_PORT": "",
    "DEBUG": false
}
```

DEBUG MODE should be set to FALSE in production.

## Gunicorn

```
pip3 install gunicorn
```

Create a file called "gunicorn_start" in /webapps/wnioskivenv/bin:

```
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

```

Add permissions

```
chmod u+x gunicorn_start
```

Check if it works

```
gunicorn_start
```

## Supervisor

```
cd /etc/supervisor/conf.d/
```

Create a file called "wnioski.conf":

```
[program:wnioski]
command = /webapps/wnioskivenv/bin/gunicorn_start                    ; Command to start app
user = root                                                          ; User to run as
stdout_logfile = /webapps/wnioskivenv/logs/gunicorn_supervisor.log   ; Where to write log messages
redirect_stderr = true                                                ; Save stderr in the same log
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8                       ; Set UTF-8 as default encoding
```

```
cd /webapps/wnioskivenv
mkdir logs
touch logs/gunicorn_supervisor.log
```

Check if supervisor works:
`supervisorctl reread`
correct response: "wnioski: available" \
`supervisorctl update` \
correct response: "wnioski: added process group"

## NGINX

```
cd /etc/nginx/sites-available/
```

Create a file called "wnioski":

```
upstream wnioski_server {
  server unix:/webapps/wnioskivenv/run/gunicorn.sock fail_timeout=0;
}

server {

    listen   80;
    server_name  YOUR IP ADDRESS;

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

```

```
cd
ln -s /etc/nginx/sites-available/wnioski /etc/nginx/sites-enabled/wnioski
```

```
service nginx restart
```

Check:

```
supervisorctl restart wnioski
```

Create a place for logs:

```
cd webapps/wnioskivenv/logs
touch nginx-access.log
touch nginx-error.log
```

## Create staticfiles, make migrations to database, createsuperuser

```
cd webapps/wnioskivenv/wnioski
```

```
python3 manage.py collectstatic
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
```
