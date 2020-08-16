from hashlib import sha1
import hmac
import json
import logging
import os

from flask import Flask, abort, flash, make_response, redirect, request, render_template, session, url_for

from eyeball import Eyeball

OAUTH_BACKENDS = [ Twitter ]

# Basic setup
app = Flask(__name__)
app.config.from_pyfile('config.py')
oauth = OAuth(app, Cache())

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

