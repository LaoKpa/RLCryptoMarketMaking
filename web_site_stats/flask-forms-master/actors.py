    
# using python 3
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextField, TextAreaField
from wtforms import *
from wtforms.widgets import *
from wtforms.validators import Required
from data import ACTORS
import random as rnd
from werkzeug.serving import run_simple

import multiprocessing
import time

def loader(filename):
    import sys, os, importlib
    sys.path.append(os.path.dirname(filename))
    mname = os.path.splitext(os.path.basename(filename))[0]
    imported = importlib.import_module(mname)                       
    sys.path.pop()
    return imported

tsc = loader('../../classical_trading/trading_stats_calculator.py')

app = Flask(__name__)
# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'some?bamboozle#string-foobar'
# Flask-Bootstrap requires this line
Bootstrap(app)
# this turns file-serving to static, using Bootstrap files installed in env
# instead of using a CDN
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

# with Flask-WTF, each web form is represented by a class
# "NameForm" can change; "(FlaskForm)" cannot
# see the route for "/" and "index.html" to see how this is used
class NameForm(FlaskForm):
    # name = StringField('Which actor is your favorite?', validators=[Required()])
    count = 0
    while True:
        try:
            profit_stats = tsc.generate_all_stats()
            break
        except Exception as e:
            print('Stats Crashed: Waiting 60 seconds.')
            time.sleep(60)
    kvl = list(profit_stats.items())
    f1 = StringField('Symbol: {0} | {1}'.format(kvl[0][0], 'Day Start'), validators=[Required()],default=str(kvl[0][1]['day_start_time']['profit']), description='')
    f2 = StringField('Symbol: {0} | {1}'.format(kvl[0][0], 'Day Ago'), validators=[Required()],default=str(kvl[0][1]['day_ago_time']['profit']), description='')
    f3 = StringField('Symbol: {0} | {1}'.format(kvl[0][0], 'Week Ago'), validators=[Required()],default=str(kvl[0][1]['week_ago_time']['profit']), description='')
    f4 = StringField('Symbol: {0} | {1}'.format(kvl[0][0], 'Month Ago'), validators=[Required()],default=str(kvl[0][1]['month_ago_time']['profit']), description='')
    f5 = StringField('Symbol: {0} | {1}'.format(kvl[1][0], 'Day Start'), validators=[Required()],default=str(kvl[1][1]['day_start_time']['profit']), description='')
    f6 = StringField('Symbol: {0} | {1}'.format(kvl[1][0], 'Day Ago'), validators=[Required()],default=str(kvl[1][1]['day_ago_time']['profit']), description='')
    f7 = StringField('Symbol: {0} | {1}'.format(kvl[1][0], 'Week Ago'), validators=[Required()],default=str(kvl[1][1]['week_ago_time']['profit']), description='')
    f8 = StringField('Symbol: {0} | {1}'.format(kvl[1][0], 'Month Ago'), validators=[Required()],default=str(kvl[1][1]['month_ago_time']['profit']), description='')

# define functions to be used by the routes (just one here)

# retrieve all the names from the dataset and put them into a list
def get_names(source):
    names = []
    for row in source:
        name = row["name"]
        names.append(name)
    return sorted(names)

# all Flask routes below

# two decorators using the same function
@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    names = get_names(ACTORS)
    # you must tell the variable 'form' what you named the class, above
    # 'form' is the variable name used in this template: index.html
    form = NameForm()
    message = ""
    if form.validate_on_submit():
        name = form.name.data
        if name in names:
            message = "Yay! " + name + "!"
            # empty the form field
            form.name.data = ""
        else:
            message = "That actor is not in our database."
    # notice that we don't need to pass name or names to the template
    return render_template('index.html', form=form, message=message)


def func():
    app.run(debug=True, host='192.168.0.32')

def func_handle():
    # Start bar as a process
    p = multiprocessing.Process(target=func)
    p.start()

    # Wait for 10 seconds or until process finishes
    p.join(50)

    # If thread is still active
    if p.is_alive():
        print("running... let's kill it...")
        # Terminate
        p.terminate()
        p.join()

# keep this as is
if __name__ == '__main__':
        func_handle()