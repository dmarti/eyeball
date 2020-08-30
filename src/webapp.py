from hashlib import sha1
import hmac
import json
import logging
import os

from flask import Flask, abort, flash, make_response, redirect, request, render_template, session, url_for

from eyeball import Eyeball

# Basic setup
app = Flask(__name__)
app.config.from_pyfile('config.py')

@app.route('/site.css')
def favicon():
    return app.send_static_file('site.css')

@app.route('/')
def home():
    strongset = eyeball.relationship.strong_set()
    return render_template('table.html', strongset=strongset) 


# startup stuff
app.logger.setLevel(logging.DEBUG)
start_demo_db = False
if 'development' == app.config.get('ENV'):
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # This is the process that will be killed and restarted.
        # Can't do anything here, so just wait for the end.
        time.sleep(3600)
    start_demo_db = True
app.logger.info("App %s started. Env is %s" % (__name__, app.config.get('ENV')))
app.logger.debug("Logging at DEBUG level.")

eyeball = Eyeball(applog=app.logger, start_demo_db=start_demo_db)
app.logger.debug("Eyeball started.")

if 'development' == app.config.get('ENV'):
    app.logger.info('''

##############################################################################
#                                                                            #
# Welcome to the local test environment.                                     #
#                                                                            #
# YOUR ACTIONS ON THIS TEST SERVER WILL NOT BE REFLECTED ON THE LIVE SERVER. #
#                                                                            #
##############################################################################
''')

