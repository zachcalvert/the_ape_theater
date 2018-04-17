# the ape

Django site powering Portland's premier comedy venue, The Ape Theater. 

Check it out here: https://theapetheater.org/


## local setup

This setup guide presumes that mysql is installed and running, and that virtualenv and virtualenvwrapper are configured on the local machine. For instructions on how to set up virtualenvwrapper (highly recommended), check out their docs:

http://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation

(installing virtualenv should be as simple as 'pip install virtualenv')


If you want to proceed without a virtual environment, just skip the 'mkvirtualenv the_ape' step below.



* 'git clone git@github.com:zachcalvert/the_ape_theater.git'
* 'cd the_ape_theater/the_ape'
* 'mkvirtualenv the_ape'
* 'pip install -r requirements.txt'
* 'echo "create database apedb CHARACTER SET utf8 COLLATE utf8_bin;" | mysql -u root -p'  (empty password)
* './manage.py migrate' 
* './manage.py collectstatic --noinput'
* './manage.py createsuperuser'  (set whatever credentials you like, just remember them!)
* './manage.py update_local'    (this will pull in all the performer/teacher data and images from the live site)
* './manage.py runserver'




Now navigate to 'http://localhost:8000/'.

The admin can be accessed at 'http://localhost:8000/admin/'. You can log into the admin with the credentials of the previously created superuser.
