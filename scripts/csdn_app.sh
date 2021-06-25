#! /bin/bash
source ~/.bash_profile
export FLASK_ENV=production
cd /home/time/Time_CSDN/Time_CSDN/
workon py3_django
exec gunicorn -b 0.0.0.0:8000 --access-logfile /home/time/logs/access_app.log --error-logfile /home/time/logs/error_app.log csdn.main:app