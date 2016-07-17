import httplib2

from datetime import datetime, timedelta
from apiclient import discovery
from oauth2client import client
from flask import Flask, session, redirect, render_template, url_for, request
from flask.ext.sqlalchemy import SQLAlchemy
from mail import mail
from dateutil.parser import parse
from pytz import utc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


# FACTOR OUT
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


# FACTOR OUT

@app.route('/')
def main():
    return render_template('index.html')


@app.route('/redirect_to_authorize', methods=['post'])
def redirect_to_authorize():
    print 'TEST TEST'
    sessions = [event.session for event in BusyTime.query.all()]
    session['coordination_id']=max(sessions) + 1 if sessions else 0,
    session['startDate']=request.form['startDate'],
    session['endDate']=request.form['endDate']
    url = url_for('authorize',
                  coordination_id=max(sessions) + 1 if sessions else 0,
                  startDate=request.form['startDate'],
                  endDate=request.form['endDate'])
    emails = (request.form[email] for email in ['email1', 'email2', 'email3'])
    message = 'Hi, coordinator would like to access your calendar. \
               Please click on '+url

    # for email in emails:
    #     mail(email, 'request from coordinator', message)
    return redirect(url)

@app.route('/authorize/<coordination_id>/<startDate>/<endDate>')
def authorize(coordination_id, startDate, endDate):
    session['coordination_id']=coordination_id
    session['startDate']=startDate
    session['endDate']=endDate
    # # CLear out old sessions_ids!
    return confirm()

@app.route('/confirm')
def confirm():
### FOR TESTING PURPOSES
    session['coordination_id']=0
    session['startDate']=datetime.today().strftime('%Y-%m-%d')
    session['endDate']=(datetime.today() + timedelta(days=5)).strftime('%Y-%m-%d')

###END TESTING
    # FACTOR OUT
    if 'credentials' not in session:
        # requests access from user
        return oauth2callback()
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return oauth2callback()
    http_auth = credentials.authorize(httplib2.Http())

    # "service" will perform all the basic functions of the Calendar API
    service = discovery.build('calendar', 'v3', http_auth)
    startDate, endDate = (session[time]+'T00:00:00Z'
            for time in ('startDate', 'endDate'))

    # eventsResult requests events in the user's calendar between
    eventsResult = service.events().list(
            ### CHANGE THIS:
        calendarId='0mninvkc7gf8fajkq991mo93to@group.calendar.google.com',
###

        timeMin=startDate,
        timeMax=endDate,
        singleEvents=True,
        orderBy='startTime').execute()

    # FACTOR OUT
    # events actually retrieves those 10 events
    events = eventsResult.get('items', [])
    for event in events:
        start, end = (parse(event[time]['dateTime'])
                      for time in ('start', 'end'))
        db.session.add(BusyTime(session['coordination_id'], start, end))

    if not events:
        return 'No upcoming events found.'

    # renders index.html in the browser and provides the 'events' variable to it
    start, end = (parse(session[time]) for time in ('startDate', 'endDate'))
    busy_times = {event.start: event.end for event in BusyTime.query.all()}
    free_times = busy_to_free(start, end, busy_times)
    formatted_free_times = (tuple(time.strftime('%A, %b %d, %Y')
            for time in times)
            for times in free_times)
    # query only the latest session
    print('busy times', busy_times)
    for times in formatted_free_times:
        print('formatted times: ',times)
    return render_template('free.html', free=formatted_free_times)

def busy_to_free(start, end, start_times):
    times = list(start_times.keys()) + list(start_times.values())
    times.sort()
    get_start = {value: key for key, value in start_times.items()}

    free, current = [], {}
    localize = lambda t: utc.localize(t) if t.tzinfo is None else t
    start, end = map(localize, (start, end))
    for time in times:
        if not current and end > start:
            free.append((start, time))
        if time in start_times:
            current[time] = start_times[time]
        else:  # time is an end time
            del current[get_start[time]]
        start = time
    return free


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
        return redirect(url_for('confirm'))


if __name__ == '__main__':
    import uuid

    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run(port=8000)
