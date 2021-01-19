import os
from db_init import initialize
from flask import Flask,Blueprint
from psycopg2 import extensions

# blueprint for routes in the app
from views import auth as auth_blueprint
from views import main as main_blueprint

extensions.register_type(extensions.UNICODE)
extensions.register_type(extensions.UNICODEARRAY)

heroku = False

if(not heroku): 
    os.environ['DATABASE_URL'] = "dbname='postgres' user='postgres' host='localhost' password='dbpassword'"
    initialize(os.environ.get('DATABASE_URL'))


app = Flask(__name__) 
app.secret_key = "verySecretKey"
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
   


if __name__ == "__main__":
    if not heroku:
        app.run(debug=True)
    else:
        app.run()