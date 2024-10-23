# Team Koala Small Group project

## Team members
The members of the team are:
- Bowen Zhu
- Saathveekan Satheeshkumar
- Augusto Favero
- Karim Mousa
- Shozab Anwar Siddique

## Project structure
The project is called `msms` (Music School Management System).  It currently consists of a single app `lessons` where all functionality resides.

## Known problems
When runserver and trying to access the webpage, a error message such as 'valueError at /'-'the view lessons.helper.modified_view_function didn't return an HttpResponse object' might come out. We think this might be becasue we push settings we made for pythonanywhere to the main is well. To solve this problem, please delete database and redo python manage.py migrate, and everything should work as normal
Altering seeded term information does not update the term information of the seeded lessons. But does for any future lessons made. 

## Deployed version of the application
The deployed version of the application can be found at http://saths008.pythonanywhere.com/ .

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.

To create a superuser for testing purposes, please use the command:

python3 manage.py createsuperuser

And use the following email:
admin@example.org

,as this user won't be deleted when the database is deleted.

From the root of the project:

If possible test our application in firefox or Google Chrome, avoid safari if possible as the bootstrap doesn't render properly.

```
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Make makemigration:

```
$ python3 manage.py makemigrations
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```

Run server with:
```
$ python3 manage.py runserver
```

*The above instructions should work in your version of the application.  If there are deviations, declare those here in bold.  Otherwise, remove this line.*

## Sources
The packages used by this application are specified in `requirements.txt`
```
asgiref==3.4.1
coverage==6.0.1
Django==3.2.5
django-widget-tweaks==1.4.8
Faker==8.10.3
humanize==3.12.0
libgravatar==1.0.0
python-dateutil==2.8.2
pytz==2021.1
six==1.16.0
sqlparse==0.4.1
text-unidecode==1.3
```
*Declare are other sources here.*

## Reference
Material we refers to when writing code
```
With Log in View in views was written, we refer to part of the code in Login View from clucker
With Sign up View in views was written, we refer to part of the code in Sginup View from clucker
With Log in Tests in tests/views was written, we refer to part of the code in test/views/test_sign_up_view from clucker
With Sign up Test in tests/views was written, we refer to part of the code in test/views/test_sign_up_view from clucker
With UserAccount model in models was written, we refer to part of the code in User model from clucker
With UserAccount model's tests in test/models was writtent, we refer to part of the code in tests/models/test_user_model from clucker
With Invoice model's tests in test/models was writtent, we refer to part of the code in tests/models/test_user_model from clucker
With Transaction model's tests in test/models was writtent, we refer to part of the code in tests/models/test_user_model from clucker
With login_required and login_prohibited in tests/helpers was written, we refer to part of the code in test/helpers from clucker
.EntryButton in static/custom.css is taken from https://getcssscan.com/css-buttons-examples
```
