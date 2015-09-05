import json
import datetime
import httplib2

from apiclient import discovery
from oauth2client import client
from flask import Flask, session, redirect, render_template, url_for, request

app = Flask(__name__)

@app.route('/')
def index():
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
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events') 

        # eventsResult requests the next 10 events in the user's calendar
        eventsResult = service.events().list(
            calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
            orderBy='startTime').execute()

    # events actually retrieves those 10 events
    events = eventsResult.get('items', [])

    if not events:
        return 'No upcoming events found.'

    # renders index.html in the browser and provides the 'events' variable to it
    return render_template('index.html', events=events)

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

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

if __name__ == '__main__':
    import uuid

    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run()
