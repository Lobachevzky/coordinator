import json
import datetime
import httplib2

from apiclient import discovery
from oauth2client import client
from flask_restful import Resource, Api, reqparse
from flask import Flask, session, redirect, render_template, url_for, request, json

app = Flask(__name__)
api = Api(app)

class CreateBusyTime(Resource):
    def post(self): 
        try:
            # Parse the arguments 
            api.add_resource(CreateBusyTime, '/CreateBusyTime')

            Parser = reqparse.RequestParser() 
            parser.add_argument('timeMin', type=str, help='start of busy time') 
            parser.add_argument('timeMax', type=str, help='end of busy time') 
            args = parser.parse_args()

            _timeMin = args['timeMin']
            _timeMax = args['timeMax']

            return {'timeMin': args['timeMin'], 'timeMax': args['timeMax']}

        except Exception as e:
            return {'error': str(e)}

api.add_resource(CreateBusyTime, '/CreateBusyTime')

@app.route('/')
def index():
    now = datetime.datetime.now()
    timeMin = now.isoformat() + 'Z'  # 'Z' indicates UTC timenow
    timeMax = (now + datetime.timedelta(days=5, hours=3)).isoformat() + 'Z'
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
    busyTimes = [(event['start']['dateTime'],event['end']['dateTime']) for event in events]
    
    if not events:
        return 'No upcoming events found.'

    # renders index.html in the browser and provides the 'events' variable to it
    return render_template('index.html', busyTimes=busyTimes)

@app.route('/showSignUp')
def showSignUp():
    return "hi"
    return render_template('signup.html')

@app.route('/signUp',methods=['POST'])
def signUp():

    # read the posted values from the UI
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']

    # validate the received values
    if _name and _email and _password:
        return json.dumps({'html':'<span>All fields good !!</span>'})
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

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
