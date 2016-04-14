import secrets

import client
from generic_oauth import SpotifyOAuth
from flask import Flask, request, make_response, render_template, send_from_directory, redirect

client_id = secrets.client_id
client_secret = secrets.client_secret
redirect_uri = secrets.redirect_uri
scope_string = secrets.scope_string

o = SpotifyOAuth(client_id, client_secret, redirect_uri, scope_string)

app = Flask(__name__)

# @app.route('/assets/<path:path>')
# def send_assets(path):
#     return send_from_directory('templates', path)

@app.route('/', methods=['GET'])
def main_page():
	access_token = request.cookies.get('access_token')
	if not access_token:
		state = o.state
		resp = make_response(render_template('./login.html', auth_url=o.authorization_url()))
		resp.set_cookie('state', state)
		return resp
	else:
		# logged in page
		access_data = {'access_token': access_token}
		resp = make_response(render_template('./desc.html', desc=client.describe_songs(access_data)))
		return resp

@app.route('/auth_code', methods=['GET'])
def index():
	state = request.cookies.get('state')
	code = request.args.get('code')

	print 'do states match? ',
	print state == o.state

	print code
	o.code = code

	try:
		access_token = o.temp_code_to_access_code()['access_token']
		resp = make_response(redirect('/'))
		resp.set_cookie('access_token', access_token)
		return resp
	except Exception, e:
		print e
		return 'ERROR'

if __name__ == "__main__":
	app.debug = True
	app.run(host="0.0.0.0", port=5555)
