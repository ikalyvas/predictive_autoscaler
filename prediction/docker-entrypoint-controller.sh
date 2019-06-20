#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:/opt/code_predict/
sleep 5 # for the service db to start up #TODO:healthcheck should be added in the ms_db service instead
#while [ "$(python manage.py wait_for_db)" != "True" ]; do
#  echo "$(date):  ms_db has not yet started" >> db_check.logs
#  sleep 3
#done
python predictor/manage.py makemigrations >> db.logs
python predictor/manage.py migrate >> db.logs
#python predictor/manage.py collectstatic --clear --noinput # clearstatic files
#python predictor/manage.py collectstatic --noinput  # collect static files
# Prepare log files and start outputting logs to stdout
python predictor/manage.py runserver 0.0.0.0:8000