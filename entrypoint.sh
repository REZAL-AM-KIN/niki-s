echo "Making migrations"
python manage.py makemigrations || exit 1
echo "Running migrations"
python manage.py migrate || exit 2
echo "Inserting base data if necessary"
echo "import insert_base_data" | python manage.py shell || { echo "Missing super user configuration. Check the environment variables."; exit 3; }
if [ "$PROD" == "True" ] && [ "$DEBUG" == "False" ]; then
  echo "Starting Server"
  log_file=/var/log/niki/gunicorn.niki.log
  if ! [ -e "$log_file" ] ; then
    mkdir -p /var/log/niki/
    touch "$log_file"
  fi
  gunicorn --bind 0.0.0.0:8000 --workers 9 --log-file $log_file niki.wsgi:application
else
  echo "Starting Development Server"
  python manage.py runserver 0:8000
fi
