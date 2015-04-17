from flask import Flask, request, jsonify
from flaskext.mysql import MySQL
from exceptions import KeyError
from _mysql_exceptions import IntegrityError
from helper import DoesNotExist, get_user_info, get_forum_info, get_thread_info, get_post_info, right_index
import MySQLdb



class InvalidArg(Exception):
	pass


mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'db_api'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
connection = mysql.connect()


def curs():
	connection.ping(True)
	return connection.cursor()

"""FORUMS"""

@app.route('/db/api/forum/create/', methods=['POST'])
def forum_create():
	cursor = curs()
	try:
		data = request.get_json()
		name = data['name']
		short_name = data['short_name']
		user = data['user']
		cursor.execute("""insert into forums (name, shortname, userEmail) 	
				   values (%s, %s, %s)""",(name, short_name, user))
		connection.commit()
		cursor.close()
		return jsonify(code=0, response={
			'id':cursor.lastrowid,
			'name':name,
			'short_name': short_name,
			'user': user})	   
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='user does not exist')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_forum_info(short_name, connection))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/details/', methods=['GET'])
def forum_details():
	try:
		forum = request.args['forum']
		related = request.args.getlist('related')
		return jsonify(code=0, response=get_forum_info(forum, connection, related))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response="not found")
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/listPosts/', methods=['GET'])
def forum_listPosts():	
	cursor = curs()
	try:
		forum = request.args['forum']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', "1970-01-01 00:00:01")
		related = request.args.getlist('related')
		cursor.execute("select max(createDate) from posts")
		max_date = cursor.fetchone()[0]

		query = """select id from posts where forum = '{}' and 
				createDate between '{}' and '{}' order by createDate {} """.format(forum, since_date, max_date, order)
		
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)
		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_post_info(i, connection, related))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
	cursor = curs()
	try:
		forum = request.args['forum']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', "1970-01-01 00:00:01")
		related = request.args.getlist('related')
		cursor.execute("select max(createDate) from forums")
		max_date = cursor.fetchone()[0]

		query = """select id from threads where forum = '{}' and 
				createDate between '{}' and '{}' order by createDate {} """.format(forum, since_date, max_date, order)
		
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)
		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_thread_info(i, connection, related))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/listUsers/', methods=['GET'])
def forum_listUsers():
	cursor = curs()
	try:
		forum = request.args['forum']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_id = request.args.get('since_id', 0)
		related = request.args.getlist('related')

		cursor.execute("select max(id) from posts")
		max_id = cursor.fetchone()[0]
		query = """select distinct userEmail from posts join users on 
		users.email = posts.userEmail where posts.forum = '{}' and
		posts.id between {} and {} order by users.name {} """.format(forum, since_id, max_id, order)

		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)
		
		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_user_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

"""USERS"""
@app.route('/db/api/user/create/', methods=['POST'])
def user_create():
	try:
		cursor = curs()
		data = request.get_json()
		#for k, v in data.values():
		#	data[k] = MySQLdb.escape_string(v)
		name = data['name']
		username = data['username']
		email = data['email']
		about = data['about']
		isAnonymous = data.get('isAnonymous', False)
		cursor.execute("""insert into users (name, username, email, about, isAnonymous)
		VALUES (%s, %s, %s, %s, %s)""",(name, username, email, about, isAnonymous))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"id": cursor.lastrowid,
							 "name":name,
							 "username":username,
							 "email":email,
							 "isAnonymous":bool(isAnonymous),
							 "about":about
							})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=5,response='user alredy exist')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/follow/', methods=["POST"])
def user_follow():
	cursor = curs()
	try:
		data = request.get_json()
		follower = data['follower']
		followee = data['followee']
		cursor.execute("insert into follows (follower, followee) VALUES (%s, %s)",(follower,followee))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_user_info(follower, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_user_info(follower, connection))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')
	
@app.route('/db/api/user/unfollow/', methods=['POST'])
def user_unfollow():
	cursor = curs()
	try:
		data = request.get_json()
		follower = data['follower']
		followee = data['followee']
		cursor.execute("delete from follows where followee = %s and follower = %s",(followee, follower))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_user_info(follower, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_user_info(follower, connection))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/details/', methods=['GET'])
def user_details():
	try:
		user = request.args['user']
		return jsonify(code=0, response=get_user_info(user, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_user_info(user, connection))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/listFollowers/', methods=['GET'])
def user_listFollowers():
	try:
		cursor = curs()
		user = request.args['user']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_id = request.args.get('since_id', 0)
		cursor.execute("select max(id) from users")
		max_id = cursor.fetchone()[0]
		query = """select follows.follower from follows join users on follows.follower = users.email and 
		follows.followee = '{}'
		where users.id between {} and {}
		order by follows.follower {} """.format(user, since_id, max_id, order)
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)
		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_user_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/listFollowing/', methods=['GET'])
def user_listFollowing():
	cursor = curs()
	try:
		user = request.args['user']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_id = request.args.get('since_id', 0)
		cursor.execute("select max(id) from users")
		max_id = cursor.fetchone()[0]
		query = """select follows.followee from follows join users on follows.followee = users.email and 
		follows.follower = '{}'
		where users.id between {} and {}
		order by follows.followee {} """.format(user, since_id, max_id, order)
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)
		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_user_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_update():
	cursor = curs()
	try:
		data = request.get_json()
		name = data['name']
		user = data['user']
		about = data['about']
		cursor.execute("update users set name = %s, about = %s where email = %s",(name, about, user))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_user_info(user, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
	cursor = curs()
	try:
		user = request.args['user']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', "1970-01-01 00:00:01")
		cursor.execute("select max(createDate) from posts")
		max_date = cursor.fetchone()[0]

		query = """select id from posts where userEmail = '{}' and 
				createDate between '{}' and '{}' order by createDate {} """.format(user, since_date, max_date, order)
		
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)

		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_post_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

"""Threads"""

@app.route('/db/api/thread/create/', methods=['POST'])
def thread_create():
	cursor = curs()
	try:
		data = request.get_json()
		date = data['date']
		user = data['user']
		slug = data['slug']
		forum = data['forum']
		title = data['title']
		closed = int(data['isClosed'])
		message = data['message']
		deleted =  int(bool(data.get('isDeleted')))

		cursor.execute("""insert into threads (createDate, forum, isClosed, isDeleted,
					   message, slug, title, userEmail) 	
				       values (%s, %s, %s, %s, %s,
				   	   %s, %s, %s)""",(date, forum, closed, deleted, message, slug, title, user))
		connection.commit()
		cursor.close()
		return jsonify(code=0, response={
			'id':cursor.lastrowid,
			'date':date,
			'forum': forum,
			'isClosed': bool(closed),
			'isDeleted': bool(deleted),
			'message': message,
			'slug': slug,
			'title': title,
			'user': user})	   
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/details/", methods=["GET"])
def thread_details():
	try:
		thread = request.args['thread']
		related = request.args.getlist('related')
		if not all(i in ('user', 'forum') for i in related): raise InvalidArg
		return jsonify(code=0, response=get_thread_info(thread, connection, related))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=2, response='something not found')
	except InvalidArg:
		return jsonify(code=3, response='wrong args')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/subscribe/", methods=["POST"])
def thread_subscribe():
	cursor = curs()
	try:
		data = request.get_json()
		user = data['user']
		thread = data['thread']
		cursor.execute("insert into subscribes (userEmail, thread) VALUES (%s, %s)",(user, thread))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"thread": thread, "user": user})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response={"thread": thread, "user": user})
		elif e[0] == 1452:
			return jsonify(code=1, response='user or thread not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/unsubscribe/", methods=["POST"])
def thread_unsubscribe():
	cursor = curs()
	try:
		data = request.get_json()
		user = data['user']
		thread = data['thread']
		cursor.execute("delete from subscribes where userEmail = %s and thread = %s",(user, thread))
		connection.commit()
		cursor.close()
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except:
		return jsonify(code=4, response='opps')
	return jsonify(code=0, 
				   response={"thread": thread, "user": user})

@app.route("/db/api/thread/update/", methods=['POST'])
def thread_update():
	cursor = curs()
	try:
		data = request.get_json()
		message = data['message']
		slug = data['slug']
		thread = data['thread']
		cursor.execute("update threads set message = %s, slug = %s where id = %s",(message, slug, thread))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_thread_info(thread, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/close/", methods=['POST'])
def thread_close():
	cursor = curs()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("update threads set isClosed = 1 where id = %s",(thread,))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"thread": thread})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='thread not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/open/", methods=['POST'])
def thread_open():
	cursor = curs()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("update threads set isClosed = 0 where id = %s",(thread,))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"thread": thread})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/remove/", methods=['POST'])
def thread_remove():
	cursor = curs()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("""update threads set isDeleted = 1 where id = %s""",(thread,))
		cursor.execute("""update posts set isDeleted = 1 where thread = %s""", (thread,))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"thread": thread})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/restore/", methods=['POST'])
def thread_restore():
	cursor = curs()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("""update threads set isDeleted = 0 where id = %s""",(thread,))
		cursor.execute("""update posts set isDeleted = 0 where thread = %s""", (thread,))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"thread": thread})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/vote/", methods=['POST'])
def thread_vote():
	cursor = curs()
	try:
		data = request.get_json()
		vote = data['vote']
		thread = data['thread']
		if vote == 1:
			cursor.execute("update threads set likes = likes + 1 where id = %s",(thread,))
		else:
			cursor.execute("update threads set dislikes = dislikes + 1 where id = %s",(thread,))

		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_thread_info(thread, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/list/", methods=['GET'])
def thread_list():
	cursor = curs()
	try:
		user = request.args.get('user', False)
		forum = request.args.get('forum', False)

		if ((user and forum) or not (user or forum)): raise Exception('only one')

		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', "1970-01-01 00:00:01")
		
		cursor.execute("select max(createDate) from threads")
		max_date = cursor.fetchone()[0]

		if user:
			query = """select id from threads where userEmail = '{}' """.format(user)
		else:
			query = """select id from threads where forum = '{}' """.format(forum)

		query += """ and createDate between '{}' and '{}' 
		order by createDate {} """.format(since_date, max_date, order)
		
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)

		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_thread_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/listPosts/", methods=['GET'])
def thread_listPosts():
	cursor = curs()
	try:
		thread = request.args['thread']

		limit = request.args.get('limit', '')
		sort = request.args.get('sort', 'flat')
		order = request.args.get('order', 'desc')
		
		since_date = request.args.get('since', "1970-01-01 00:00:01")
		
		cursor.execute("select max(createDate) from posts")
		max_date = cursor.fetchone()[0]
		
		
		if sort == 'flat':
			query = """select id from posts where thread = {}""".format(thread)
			query += """ and createDate between '{}' and '{}' order by """.format(since_date, max_date)
			query += 'createDate {} '.format(order)
			query += "limit {}".format(limit) if limit != '' else ''

		elif sort == 'tree':
			query = """select p2.id from posts as p join posts as p2 on p2.mpath 
					like CONCAT(p.mpath,'%') and p.parent is null and thread = {} and createDate between '{}' and '{}'
					order by p.mpath {} {};""".format(thread, since_date, max_date, order, 
											   "limit {}".format(limit) if limit != '' else '')
		else:
			query = """select p2.id from posts as p2 join 
			(select p.mpath, p.id from posts as p where parent is null {} ) as p 
			on p2.mpath like CONCAT(p.mpath,'%') and thread = {} and createDate between '{}' and '{}' 
			order by p.mpath {}""".format("limit {}".format(limit) if limit != '' else '',
									thread, since_date, max_date, order)
		
		cursor.execute(query)
		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_post_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

"""POSTS"""
@app.route('/db/api/post/create/', methods=['POST'])
def post_create():
	cursor = curs()
	try:
		data = request.get_json()

		date = data["date"]
		thread = data["thread"]
		message = data["message"]
		user = data["user"]
		forum = data["forum"]

		parent = data.get("parent", None)
		isApproved = data.get("isApproved", False)
		isHighlighted = data.get("isHighlighted", False)
		isEdited = data.get("isEdited", False)
		isSpam = data.get("isSpam", False)
		isDeleted = data.get("isDeleted", False)
		cursor.execute("""insert into posts (createDate, forum, isHighlighted, isApproved,
						isDeleted, isEdited, isSpam, message, parent, thread, userEmail) 	
				   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)""",
				   (date, forum, isHighlighted, isApproved, isDeleted, isEdited, isSpam,
				   	message, parent, thread, user))
		lid = cursor.lastrowid
		if parent:
			cursor.execute("select mpath from posts where id = {}".format(parent))
			parent_mpath = cursor.fetchone()[0]+right_index(lid)
		else:
			parent_mpath = right_index(lid)
		cursor.execute("update posts set mpath = '{}/' where id = {}".format(parent_mpath,lid))
		cursor.close()

		connection.commit()
		return jsonify(code=0, response={
			'id':lid,
			"date": date,
        	"forum": forum,
        	"isApproved": isApproved,
        	"isDeleted": isDeleted,
        	"isEdited": isEdited,
        	"isHighlighted": isHighlighted,
        	"isSpam": isSpam,
        	"message": message,
       		"parent": parent,
        	"thread": thread,
        	"user": user})	   
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='post does not exist')
	except:
		return jsonify(code=4, response='opps')

	#except IntegrityError, e:
	#	if e[0] == 1062:
	#		return jsonify(code=2, response=get_post_info(short_name, connection))
	#	elif e[0] == 1452:
	#		return jsonify(code=2, response='user not found')
	#except:
	#	return jsonify(code=2, response='bad request')

@app.route("/db/api/post/details/", methods=['GET'])
def post_details():
	try:
		post = request.args['post']
		related = request.args.getlist('related')
		return jsonify(code=0, response=get_post_info(post, connection, related))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/remove/", methods=['POST'])
def post_remove():
	cursor = curs()
	try:
		data = request.get_json()
		post = data['post']
		cursor.execute("update posts set isDeleted = 1 where id = %s",(post,))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"post": post})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/restore/", methods=['POST'])
def post_restore():
	cursor = curs()
	try:
		data = request.get_json()
		post = data['post']
		cursor.execute("update posts set isDeleted = 0 where id = %s",(post,))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response={"post": post})
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/vote/", methods=['POST'])
def post_vote():
	cursor = curs()
	try:
		data = request.get_json()
		vote = data['vote']
		post = data['post']
		if vote == 1:
			cursor.execute("update posts set likes = likes + 1 where id = %s",(post,))
		else:
			cursor.execute("update posts set dislikes = dislikes + 1 where id = %s",(post,))

		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_post_info(post, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/update/", methods=['POST'])
def post_update():
	cursor = curs()
	try:
		data = request.get_json()
		post = data['post']
		message = data['message']
		cursor.execute("update posts set message = %swhere id = %s",(message, post))
		connection.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_post_info(post, connection))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/list/", methods=['GET'])
def post_list():
	cursor = curs()
	try:
		thread = request.args.get('thread', False)
		forum = request.args.get('forum', False)

		if ((thread and forum) or not (thread or forum)): raise Exception('only one')

		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', "1970-01-01 00:00:01")
		
		cursor.execute("select max(createDate) from posts")
		max_date = cursor.fetchone()[0]

		if thread:
			query = """select id from posts where thread = {} """.format(thread)
		else:
			query = """select id from posts where forum = '{}' """.format(forum)

		query += """ and createDate between '{}' and '{}' order by createDate {} """.format(since_date, max_date, order)
		
		query += "limit {}".format(limit) if limit != '' else ''
		cursor.execute(query)

		a = []
		for i in tuple(t[0] for t in cursor.fetchall()):
			a.append(get_post_info(i, connection))
		cursor.close()
		return jsonify(code=0, response=a)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

"""OTHER"""
@app.route('/db/api/clear/', methods=['POST'])
def clear():
	try:
		cursor = curs()
		cursor.execute("""delete from users""");
		connection.commit()
		cursor.close()
		return jsonify(code=0, response="OK")
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/status/", methods=['GET'])
def status():
	try:
		cursor = curs()
		cursor.execute("select count(*) from users")
		count_users = cursor.fetchone()[0]
		cursor.execute("select count(*) from forums")
		count_forums = cursor.fetchone()[0]
		cursor.execute("select count(*) from threads")
		count_threads = cursor.fetchone()[0]
		cursor.execute("select count(*) from posts")
		count_posts = cursor.fetchone()[0]
		return jsonify(code=0, response={"user":count_users,
										"forum":count_forums,
										"thread": count_threads,
										"posts": count_posts})
	except:
		return jsonify(code=4, response='opps')

if __name__ == '__main__':
	app.run(debug=True)
