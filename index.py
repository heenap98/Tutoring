from flask import Flask, jsonify, make_response, request, render_template
import urlparse
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__, static_url_path='')

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse('postgresql://localhost:5432/tutoring')
db = psycopg2.connect(database=url.path[1:],
	user=url.username,
	password=url.password,
	host=url.hostname,
	port=url.port)

@app.route('/testdb')
def test():
	with db.cursor() as cur:
		try:
			cur.execute('SELECT * FROM tutors')
			return jsonify({"success": True, "data": str(cur.fetchall())})
		except psycopg2.DatabaseError as e:
			return jsonify({"success": False, "msg": str(e)})

@app.route('/ping')
def ping():
	return "atlanta28ne3"

@app.route('/', methods=['GET'])
def index():
	return app.send_static_file('index.html')

@app.route('/login', methods=['GET', 'POST'])
def teacher_login():
	if request.method == 'POST':
		if validate_creds(request.form['email'], request.form['password']):

			query = 'select * from tutors where email=%s'
			with db.cursor(cursor_factory = psycopg2.extras.DictCursor) as cur:
				try:
					cur.execute(query, (request.form['email'],))
					row = cur.fetchone()
					name = row['name']
					college = row['college']
					subjects = row['subjects']
					email = row['email']
					return render_template('teacher-profile.html', name=name, email=email, college=college, subjects=subjects)
				except psycopg2.DatabaseError:
					return app.send_static_file('teacher-login.html')
		else:
			return app.send_static_file('teacher-login.html')
	return app.send_static_file('teacher-login.html')

@app.route('/update', methods=['GET', 'POST'])
def teacher_update():
	if request.method == 'POST':
		if validate_creds(request.form['email'], request.form['password']):

			query = 'select * from tutors where email=%s'
			with db.cursor(cursor_factory = psycopg2.extras.DictCursor) as cur:
				try:
					cur.execute(query, (request.form['email'],))
					row = cur.fetchone()
					name = row['name']
					college = row['college']
					subjects = row['subjects']
					email = row['email']
					return render_template('update-teacher-profile.html', name=name, email=email, college=college, subjects=subjects)
				except psycopg2.DatabaseError:
					return app.send_static_file('teacher-login.html')
		else:
			return app.send_static_file('teacher-login.html')
	return app.send_static_file('teacher-login.html')


@app.route('/api/registration', methods=['POST'])
def register():
	body = request.form

	name = body.get("name")
	email = body.get("email")
	college = body.get("college")
	subjects = body.get("subjects")
	password = body.get("password")

	return insert_teacher_into_database(name, email, college, subjects, password)

@app.route('/api/update', methods=['POST'])
def update():
	body = request.form

	email = body.get("email")
	college = body.get("college")
	subjects = body.get("subjects")
	password = body.get("password")

	return update_teacher(email, college, subjects, password)

@app.route('/api/search', methods=['GET'])
def search():
	query = request.args.get('query')
	query.replace(" ", "")
	query = query.lower()
	tutors = []
	with db.cursor(cursor_factory = psycopg2.extras.DictCursor) as cur:
		try:
			cur.execute('SELECT * FROM tutors WHERE subjects @> ARRAY[%s]', (query,))
			for row in cur:
				temp = {}
				temp['name'] = row['name']
				temp['email'] = row['email']
				temp['subjects'] = row['subjects']
				temp['college'] = row['college']
				tutors.append(temp)
		except psycopg2.DatabaseError as e:
			db.rollback()
			return jsonify({"success": False})
		else:
			db.commit()
			return jsonify({"success": True, "results": tutors})


def insert_teacher_into_database(name, email, college, subjects, password):
	with db.cursor() as cur:
		try:
			subjects = subjects.lower()
			subjects = "{" + subjects + "}"
			cur.execute('INSERT INTO tutors (name, email, college, subjects, password) VALUES (%s, %s, %s, %s, %s)', (name, email, college, subjects, password))
		except psycopg2.DatabaseError as e:
			db.rollback()
			return jsonify({"success": False})
		else:
			db.commit()
			return jsonify({"success": True})

def update_teacher(email, college, subjects, password):
	query = 'UPDATE tutors SET'
	count = 0
	if college != None:
		query += " college = '{}'".format(college)
		count += 1
	if subjects != None:
		if count != 0:
			query += ","
		query += " subjects = '{%s}'" % (subjects)
		count += 1
	if password != None:
		if count != 0:
			query += ","
		query += " password = '{}'".format(password)

	with db.cursor() as cur:
		try:
			cur.execute(str(query) + ' WHERE email = %s', (email,))
		except psycopg2.DatabaseError as e:
			db.rollback()
			return jsonify({"success": False, "message": str(e)})
		else:
			db.commit()
			return jsonify({"success": True})

def validate_creds(email, password):
	query = 'select count(*) from tutors where email=%s and password=%s'
	with db.cursor(cursor_factory = psycopg2.extras.DictCursor) as cur:
		try:
			cur.execute(query, (email, password))
			row = cur.fetchone()
			if row['count'] != 1:
				return False
			else:
				return True
		except psycopg2.DatabaseError:
			return False


if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)
