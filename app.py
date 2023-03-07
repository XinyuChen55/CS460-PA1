######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'yyqxyzdys'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='False')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		birth=request.form.get('birth')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	gender=request.form.get('gender')
	hometown=request.form.get('hometown')
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, birth, gender, hometown) VALUES\
		       ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, first_name, last_name, birth, gender, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('error'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, pid, caption, aid FROM Pictures WHERE uid = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUsersAlbums(uid):
	cursor=conn.cursor()
	cursor.execute("SELECT aid, aname FROM Albums WHERE uid = '{0}'".format(uid))
	return cursor.fetchall() #return a list of aid and names of albums

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT uid FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]
	
def getAlbumIdFromName(uid, name):
	cursor = conn.cursor()
	cursor.execute("SELECT aid FROM Albums WHERE uid = '{0}' and aname = '{1}'".format(uid, name))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def ifAlbumExist(uid, aname):
	cursor = conn.cursor
	if cursor.execute("SELECT * FROM Albums WHERE uid = '{0}' and aname = '{1}'".format(uid, aname)):
		return True
	else:
		False

#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		aid = request.form.get('album')
		tags=request.form.get('tags')
		taglist=tags.split(",")
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, uid, caption, aid) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, aid))
		cursor.execute("SELECT LAST_INSERT_ID() AS pid")
		pid=cursor.fetchone()[0]
		cursor.execute('''INSERT INTO contains (aid, pid) VALUES ('{0}', '{1}')'''.format(aid, pid))
		for tag in taglist:
			cursor.execute("SELECT tid FROM Tags WHERE name=%s", tag.strip())
			row = cursor.fetchone()
			if row:
				tid=row[0]
			else:
				cursor.execute('''INSERT INTO Tags (name) VALUES ('{0}')'''.format(tag.strip()))
				cursor.execute("SELECT LAST_INSERT_ID() AS tid")
				tid=cursor.fetchone()[0]
			cursor.execute("INSERT INTO relate_to (pid, tid) VALUES ('{0}', '{1}')".format(pid, tid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		albums=getUsersAlbums(uid)
		return render_template('upload.html', albums=albums)
#end photo uploading code

#album code
@app.route('/create', methods=['GET','POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aname = request.form.get('name')
		cursor = conn.cursor()
		cursor.execute("SELECT aid FROM Albums WHERE aname='{0}' and uid='{1}'".format(aname, uid))
		exist=cursor.fetchall()
		if exist:
			return render_template('album.html', message="Album already exists!")
		cursor.execute('''INSERT INTO Albums (uid, aname) VALUES (%s, %s )''', (uid, aname))
		cursor.execute("SELECT LAST_INSERT_ID() AS aid")
		aid = cursor.fetchone()
		cursor.execute('''INSERT INTO has (uid, aid) VALUES (%s, %s)''', (uid, aid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album created!', albums=getUsersAlbums(uid))
	else:
		return render_template('album.html')

@app.route('/friend')
@flask_login.login_required
def all_friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name FROM Users WHERE uid in (SELECT uid2 FROM is_friend WHERE uid1='{0}')".format(uid))
	friends = cursor.fetchall()
	conn.commit()
	message = request.args.get('message')
	return render_template('friend.html', friends = friends, message = message)

@app.route('/search_friend', methods=['GET', 'POST'])
@flask_login.login_required
def search_friend():
	if request.method == 'POST':
		uid1 = getUserIdFromEmail(flask_login.current_user.id)
		email = request.form.get('email')
		cursor = conn.cursor()
		cursor.execute("SELECT uid, first_name, last_name FROM Users WHERE email = '{0}'".format(email))
		result = cursor.fetchone()
		uid2=result[0]
		fname=result[1]
		lname=result[2]
		cursor.execute("SELECT uid2 FROM is_friend WHERE uid1='{0}' and uid2='{1}'".format(uid1, uid2))
		friend=cursor.fetchall()
		conn.commit()
		if friend:
			return render_template('search_friend.html', message='Your are already friends!')
		return render_template('add_friend.html', uid2=uid2, fname=fname, lname=lname)
	else:
		return render_template('search_friend.html')

@app.route('/add_friend/<int:uid2>', methods=['GET'])
@flask_login.login_required
def add_friend(uid2):
	uid1 = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute('''INSERT INTO is_friend (uid1, uid2) VALUES (%s, %s)''', (uid1, uid2))
	conn.commit()
	return render_template('hello.html', name=flask_login.current_user.id, message = "New friend added")

@app.route('/browse_photo')
def browse_photo():
    cursor = conn.cursor()
    cursor.execute("SELECT P.pid, P.caption, P.imgdata, A.aname, U.first_name, U.last_name, U.uid, \
		(SELECT COUNT(*) FROM likes WHERE pid=P.pid) AS likes, \
		(SELECT GROUP_CONCAT(CONCAT_WS(':', C.text, U2.first_name, U2.last_name)) FROM Pictures P1 JOIN (Comments C JOIN Users U2 ON C.uid=U2.uid) ON P1.pid=C.pid WHERE P1.pid=P.pid) AS comments \
		FROM Pictures P \
		JOIN Users U ON P.uid=U.uid \
		JOIN contains Con ON P.pid=Con.pid \
        JOIN Albums A ON Con.aid=A.aid ")
    pictures = cursor.fetchall()
    cursor.execute("SELECT text, pid FROM Comments WHERE uid=-1")
    visitors=cursor.fetchall()
    conn.commit()
    return render_template('browse_photo.html', pictures=pictures, visitors=visitors, base64=base64)

@app.route('/browse_album')
def browse_album():
	cursor = conn.cursor()
	cursor.execute("SELECT aid, aname, first_name, last_name FROM Albums A JOIN Users U ON U.uid=A.uid")
	albums = cursor.fetchall()
	conn.commit()
	return render_template('browse_album.html', albums=albums)

@app.route('/view_album/<int:aid>')
def view_album(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT pid, caption, imgdata, aname FROM Pictures P JOIN Albums A ON P.aid= A.aid WHERE A.aid = '{0}'".format(aid))
    photos = cursor.fetchall()
    aname = "Unkown"
    for photo in photos:
        if photo[3] is not None:
            aname = photo[3]
            break
    conn.commit()
    return render_template('view_album.html', photos=photos, aname=aname, base64=base64)

@app.route('/delete_photo')
@flask_login.login_required
def your_photo():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photos=getUsersPhotos(uid)
	return render_template('delete_photo.html', photos=photos, base64=base64)

@app.route('/delete_photo/<int:pid>')
@flask_login.login_required
def delete_photo(pid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, pid FROM Pictures WHERE pid='{0}' and uid='{1}'".format(pid, uid))
	photo = cursor.fetchone()
	conn.commit()
	return render_template('delete_photo.html', delete=True, base64=base64, photo=photo)
	
@app.route('/delete_photo/<int:pid>/confirm')
@flask_login.login_required
def confirm_delete_photo(pid):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pictures WHERE pid='{0}'".format(pid))
    conn.commit()
    return render_template('hello.html', message='Photo successfully deleted')

@app.route('/delete_album')
@flask_login.login_required
def your_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums=getUsersAlbums(uid)
	return render_template('delete_album.html', albums=albums)

@app.route('/delete_album/<int:aid>')
@flask_login.login_required
def delete_album(aid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT aid, aname FROM Albums WHERE aid='{0}' and uid='{1}'".format(aid, uid))
	album = cursor.fetchone()
	conn.commit()
	return render_template('delete_album.html', delete=True, album=album)
	
@app.route('/delete_album/<int:aid>/confirm')
@flask_login.login_required
def confirm_delete_album(aid):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Albums WHERE aid='{0}'".format(aid))
    cursor.execute("DELETE FROM Pictures WHERE pid IN \
		   (SELECT pid FROM contains WHERE aid='{0}')".format(aid))
    conn.commit()
    return render_template('hello.html', message='Album successfully deleted')

@app.route('/view_by_tag')
def view_by_tag():
	return render_template('view_by_tag.html')

@app.route('/my_tag')
@flask_login.login_required
def my_tag():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT tid, name FROM Tags WHERE tid IN \
		(SELECT tid FROM relate_to WHERE pid IN \
		(SELECT pid FROM Pictures WHERE uid='{0}'))".format(uid))
	tags = cursor.fetchall()
	conn.commit()
	return render_template('my_tag.html', tags=tags)

@app.route('/my_tag/<int:tid>')
@flask_login.login_required
def view_mytag(tid):
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT P.pid, P.caption, P.imgdata FROM Pictures P JOIN relate_to R ON P.pid=R.pid WHERE R.tid='{0}' and P.uid='{1}'".format(tid, uid))
	photos = cursor.fetchall()
	cursor.execute("SELECT name FROM Tags WHERE tid='{0}'".format(tid))
	name = cursor.fetchone()[0]
	conn.commit()
	return render_template('view_tag.html', photos=photos, name=name, base64=base64)

@app.route('/all_tag')
def all_tag():
	cursor = conn.cursor()
	cursor.execute("SELECT tid, name FROM Tags")
	tags = cursor.fetchall()
	conn.commit()
	return render_template('all_tag.html', tags=tags)

@app.route('/all_tag/<int:tid>')
def view_alltag(tid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.pid, P.caption, P.imgdata FROM Pictures P JOIN relate_to R ON P.pid=R.pid WHERE R.tid='{0}'".format(tid))
	photos = cursor.fetchall()
	cursor.execute("SELECT name FROM Tags WHERE tid='{0}'".format(tid))
	name = cursor.fetchone()[0]
	conn.commit()
	return render_template('view_tag.html', photos=photos, name=name, base64=base64)

@app.route('/popular_tag')
def get_most_popular_tags():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT T.name, COUNT(R.tid) AS count
        FROM Tags T
        JOIN relate_to R ON T.tid = R.tid
        GROUP BY T.tid
        ORDER BY count DESC
		LIMIT 3
    """)
    results = cursor.fetchall()
    conn.commit()
    return render_template('popular_tag.html', results=results)

@app.route('/search_tag', methods=['POST','GET'])
def search_tag():
	if request.method == 'POST':
		tags = request.form.get('tags')
		tags =tags.split(',')
		tags = [tag.strip() for tag in tags]
		cursor = conn.cursor()
		cursor.execute("SELECT tid FROM Tags WHERE name IN ({0})".format(', '.join(['%s']*len(tags))), tags)
		tids = [t[0] for t in cursor.fetchall()]
		cursor.execute("SELECT P.pid, P.caption, P.imgdata \
	  					FROM Pictures P JOIN relate_to R ON P.pid=R.pid \
	  					WHERE R.tid IN ({0}) \
	  					GROUP BY P.pid \
		 				HAVING COUNT(DISTINCT R.tid)='{1}'".format(', '.join(['%s']*len(tids)), len(tids)), tids)
		photos=cursor.fetchall()
		conn.commit()
		return render_template('search_tag.html', photos=photos, tags=tags, base64=base64)
	else:
		return render_template('search_tag.html')
	
@app.route('/like_photo/<int:pid>')
def like_photo(pid):
	cursor = conn.cursor()
	if flask_login.current_user.is_authenticated:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	else:
		uid=-1
	cursor.execute("INSERT INTO likes (pid, uid) VALUES ('{0}', '{1}')".format(pid, uid))
	conn.commit()
	return flask.redirect(flask.url_for('browse_photo'))

@app.route('/comment_photo/<int:pid>', methods=['POST', 'GET'])
def comment_photo(pid):
    cursor=conn.cursor()
    if flask_login.current_user.is_authenticated:
        uid = getUserIdFromEmail(flask_login.current_user.id)
    else:
        uid = -1
    text = request.form.get('comment')
    cursor.execute("SELECT uid FROM Pictures WHERE pid='{0}'".format(pid))
    uid_pho=cursor.fetchone()[0]
    if uid_pho != uid:
        cursor.execute("INSERT INTO Comments (pid, uid, text) VALUES (%s, %s, %s)", (pid, uid, text))
        cursor.execute("SELECT LAST_INSERT_ID() AS cid")
        cid=cursor.fetchone()[0]
        cursor.execute("INSERT INTO makes (pid, uid, cid) VALUES (%s, %s, %s)", (pid, uid, cid))
        cursor.execute("INSERT INTO left_on (cid, pid) VALUES ('{0}','{1}')".format(cid, pid))
        conn.commit()
    return flask.redirect(flask.url_for('browse_photo'))

@app.route('/search_comment', methods=['POST', 'GET'])
def search_comment():
    if request.method == 'POST':
        text = request.form.get('text')
        cursor = conn.cursor()
        cursor.execute("SELECT U.uid, U.first_name, U.last_name, COUNT(*) AS comment_count FROM Users U \
                        JOIN Comments C ON U.uid=C.uid WHERE C.text = %s \
                        GROUP BY U.uid ORDER BY comment_count DESC", (text,))
        user_comments = cursor.fetchall()
        conn.commit()
        return render_template('search_comment.html', user_comments=user_comments, text=text)
    return render_template('search_comment.html')

@app.route('/top_contributors')
def top_contributors():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT U.uid, U.first_name, U.last_name, 
               COUNT(DISTINCT P.pid) AS photo_count, 
               COUNT(DISTINCT C.cid) AS comment_count,
               COUNT(DISTINCT P.pid) + COUNT(DISTINCT C.cid) AS score
        FROM Users U
        LEFT JOIN Pictures P ON U.uid = P.uid
        LEFT JOIN Comments C ON U.uid = C.uid
        GROUP BY U.uid
        ORDER BY score DESC
        LIMIT 10;
    """)
    #I join Users, Pictures and Comments table together. So we can count how many photos/comments each user has
	#by counting the number of pid/cid correspongding to their uid.
	#Then we have total number of photos and comments as users contribution score.
	#Then we partition table into groups by different users.
	#Lastly, we make table in descending order and return first 10 rows.
    tops = cursor.fetchall()
    conn.commit()
    return render_template('top_contributors.html', tops=tops, enumerate=enumerate)

@app.route('/recommend_friends')
@flask_login.login_required
def recommend_friends():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT F2.uid2, COUNT(*) AS num, U.first_name, U.last_name\
		   			FROM is_friend F2 JOIN Users U ON F2.uid2=U.uid\
		   			WHERE F2.uid1 IN (SELECT F1.uid2 FROM is_friend F1 WHERE (F1.uid1=%s) AND F2.uid2!=%s)\
		   					AND F2.uid2 NOT IN (SELECT F3.uid2 FROM is_friend F3 WHERE (F3.uid1=%s))\
		   			GROUP BY F2.uid2\
		   			ORDER BY num DESC", (uid, uid, uid))
    friends = cursor.fetchall()
    return render_template('recommend_friends.html', friends=friends)

@app.route('/may_like')
@flask_login.login_required
def may_like():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor=conn.cursor()

	cursor.execute("SHOW TABLES LIKE 'top_tags'") #check if table already exists.
	table_exists = cursor.fetchone() #return a non-None value if exists, None if not exists
	if not table_exists:
		cursor.execute("""
			CREATE TEMPORARY TABLE top_tags
			SELECT T.tid
			FROM Pictures P
			JOIN relate_to R ON P.pid=R.pid
			JOIN Tags T ON T.tid=R.tid
			WHERE P.uid='{0}'
			GROUP BY T.tid
			ORDER BY COUNT(*) DESC
			LIMIT 3
		""".format(uid)) #find tids of the 3 most frequently used tags by the user

	cursor.execute("""
		SELECT P.pid, P.caption, P.imgdata, U.first_name, U.last_name, GROUP_CONCAT(T.name SEPARATOR ',') AS tags
		FROM Pictures P
		JOIN Users U ON U.uid=P.uid
		JOIN relate_to R ON R.pid=P.pid
		JOIN Tags T ON T.tid=R.tid
		JOIN top_tags TT ON T.tid=TT.tid
		WHERE P.uid != '{0}'
		GROUP BY P.pid
		ORDER BY LENGTH(tags) DESC, COUNT(T.tid) ASC
	""".format(uid))

	photos=cursor.fetchall()
	return render_template('may_like.html', photos=photos, base64=base64)


#error code
@app.route('/error')
def error():
	return render_template('error.html')

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
