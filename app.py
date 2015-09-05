import json
import datetime
import httplib2
import datetime
import dateutil.parser

from apiclient import discovery
from oauth2client import client
from flask_restful import Resource, Api, reqparse
from flask import Flask, session, redirect, render_template, url_for, request, json
from flask.ext.mysql import MySQL
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class BusyTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.Integer)
    start = db.Column(db.DateTime(timezone=False))
    end = db.Column(db.DateTime(timezone=False))

    def __init__(self, session, start, end):
        self.session = session
        self.start = start
        self.end = end

    def __repr__(self):
        return '<Event %r>' % self.id

@app.route('/')
def index():
## CLear out old sessions!
# user SESSION CHANGE THIS #
    user_session = 1
    timeMin = datetime.datetime.now()
    timeMax = timeMin + datetime.timedelta(days=5, hours=3)
#user input date range
    timeMin, timeMax = (time.isoformat() + 'Z' for time in (timeMin, timeMax))

    if 'credentials' not in session:

        # requests access from user
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())

        # "service" will perform all the basic functions of the Calendar API
        service = discovery.build('calendar', 'v3', http_auth)
        print('Getting the upcoming 10 events') 

        # eventsResult requests events in the user's calendar between 
        # timeMin and timeMax
        calendarId='0mninvkc7gf8fajkq991mo93to@group.calendar.google.com' # change this to 'primary' in final version
        eventsResult = service.events().list(
            calendarId=calendarId,
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,
            orderBy='startTime').execute()

    # events actually retrieves those 10 events
    events = eventsResult.get('items', [])
    for event in events:
        start, end = (dateutil.parser.parse(event[time]['dateTime']) 
                for time in ('start','end'))
        db.session.add(BusyTime(user_session, start, end))

    if not events:
        return 'No upcoming events found.'

    # renders index.html in the browser and provides the 'events' variable to it
    busyTimes = [(time.isoformat() for time in (event.start, event.end))
                                   for event in BusyTime.query.all()]
#query only the latest session
    return render_template('index.html', busyTimes=busyTimes)

@app.route('/oauth2callback')
def oauth2callback():

    # builds a 'flow' object which helps the browser navigate 
    # the authentication process
    flow = client.flow_from_clientsecrets(
        'client_secret.json',
        scope='https://www.googleapis.com/auth/calendar.readonly',
        redirect_uri=url_for('oauth2callback', _external=True))

    # if the app does not currently have access, requests it from the user
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url() 
        # default Google 'allow access...' page
        return redirect(auth_uri)

    # otherwise redirects back to the main app page
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('index'))

if __name__ == '__main__':
    import uuid

    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run(port=8000)
