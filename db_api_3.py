from flask import Flask, request, jsonify
from _mysql_exceptions import IntegrityError
from helper2_0 import get_forum_info, get_user_info, get_thread_info, get_post_info, DB, right_index, DoesNotExist
import MySQLdb
from datetime import datetime



app = Flask(__name__)
app.debug = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False


db = DB()
class InvalidArg(Exception):
	pass


""" FORUMS """
@app.route('/db/api/forum/create/', methods=['POST'])
def forum_create():
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		name = data['name']
		short_name = data['short_name']
		user = data['user']
		cursor.execute("""insert into forums (name, shortname, user) 	
				   values (%s, %s, %s)""",(name, short_name, user))
		db.commit()
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
			return jsonify(code=0, response=get_forum_info(short_name, db))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/details/', methods=['GET'])
def forum_details():
	try:
		forum = request.args['forum']
		related = request.args.getlist('related')
		return jsonify(code=0, response=get_forum_info(forum, db, related))
	
	except KeyError:
		return jsonify(code=2, response='invalid json')
	
	except DoesNotExist:
		return jsonify(code=1, response="not found")
	
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/listPosts/', methods=['GET'])
def forum_listPosts():	
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		forum = request.args['forum']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', False)

		related = request.args.getlist('related')

		query = ""
		query_params = ()
		if since_date:
			query = "select * from posts where forum = %s and date >= %s order by date " + order
			query_params += (forum, since_date, )
		else: 
			query = "select * from posts where forum = %s order by date " + order
			query_params += (forum,)
			

		if limit != '':
			query += " limit " + limit
		

		cursor.execute(query, query_params)
		posts = cursor.fetchall()

		for post in posts:
			if 'user' in related:
				post.update({'user': get_user_info(post['user'], db)})
			if 'thread' in related:
				post.update({'thread': get_thread_info(post['thread'], db)})
			if 'forum' in related: 
				post.update({'forum': get_forum_info(post['forum'], db)})
			post.update({"date": str(post["date"])})


		cursor.close()
		return jsonify(code=0, response=posts)
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		forum = request.args['forum']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', False)

		related = request.args.getlist('related')
		query = ""
		query_params = ()
		if since_date:
			query = """select * from threads where forum = %s and date >= %s order by date """ + order
			query_params = (forum, since_date, )
		else:
			query = """select * from threads where forum = %s order by date """ + order
			query_params += (forum,)
		if limit != '':
			query += " limit " + limit


		cursor.execute(query, query_params)
		threads = cursor.fetchall()

		for thread in threads:
			if 'user' in related:
				thread.update({'user': get_user_info(thread['user'], db)})
			if 'forum' in related: 
				thread.update({'forum': get_forum_info(thread['forum'], db)})
			thread.update({"date": str(thread["date"])})
		cursor.close()
		return jsonify(code=0, response=threads)
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
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		forum = request.args['forum']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_id = request.args.get('since_id', False)

		query = ""
		query_params = ()


		if since_id:
			query = """select * from users where email in 
			(select distinct user from posts where forum = %s) and id >= %s order by name """ + order
			query_params = (forum, since_id,)
		else: 
			query = """select * from users where email in 
			(select distinct user from posts where forum = %s) order by name """ + order
			query_params = (forum,)

		if limit != '':
			query += " limit " + limit
		

		cursor.execute(query, query_params)
		
		users = cursor.fetchall()
		cursor = db.get_cursor()
		for user in users:
			cursor.execute("select followee from follows where follower = %s",(user['email'],))
			follower_followee = cursor.fetchall()
			cursor.execute("select follower from follows where followee = %s",(user['email'],))
			followee_follower = cursor.fetchall()
			cursor.execute("select thread from subscribes where user = %s",(user['email'],))
			subs = cursor.fetchall()
			user.update({
				'following': list(t[0] for t in follower_followee),
				'followers': list(t[0] for t in followee_follower),
				'subscriptions': list(t[0] for t in subs)
			})
		cursor.close()
		return jsonify(code=0, response=users)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

""" USERS """


@app.route('/db/api/user/follow/', methods=["POST"])
def user_follow():
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		follower = data['follower']
		followee = data['followee']
		cursor.execute("insert into follows (follower, followee) VALUES (%s, %s)",(follower,followee,))
		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_user_info(follower, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_user_info(follower, db))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')
	
@app.route('/db/api/user/unfollow/', methods=['POST'])
def user_unfollow():
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		follower = data['follower']
		followee = data['followee']
		cursor.execute("delete from follows where followee = %s and follower = %s",(followee, follower,))
		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_user_info(follower, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_user_info(follower, db))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/create/', methods=['POST'])
def user_create():
	try:
		cursor = db.get_cursor()
		data = request.get_json()
		name = data['name']
		username = data['username']
		email = data['email']
		about = data['about']
		isAnonymous = data.get('isAnonymous', False)
		cursor.execute("""insert into users (name, username, email, about, isAnonymous)
		VALUES (%s, %s, %s, %s, %s)""",(name, username, email, about, isAnonymous))
		db.commit()
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

@app.route('/db/api/user/details/', methods=['GET'])
def user_details():
	try:
		user = request.args['user']
		return jsonify(code=0, response=get_user_info(user, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError, e:
		if e[0] == 1062:
			return jsonify(code=0, response=get_user_info(user, db))
		elif e[0] == 1452:
			return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/listFollowers/', methods=['GET'])
def user_listFollowers():
	try:
		cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
		user = request.args['user']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_id = request.args.get('since_id', False)

		query = ""
		query_params = ()
		if since_id:
			query = """select about, email, users.id, isAnonymous, name, username from follows 
			join users on follows.follower = users.email and follows.followee = %s and users.id >= %s order by name """ + order
			query_params = (user, since_id, )
		else:
			query = """select about, email, users.id, isAnonymous, name, username from follows 
			join users on follows.follower = users.email and follows.followee = %s order by name """ + order
			query_params = (user,)

		if limit != '':
			query += " limit " + limit
		cursor.execute(query, query_params)
		users = cursor.fetchall()
		cursor = db.get_cursor()
		for user in users:
			cursor.execute("select followee from follows where follower = %s",(user['email'],))
			follower_followee = cursor.fetchall()
			cursor.execute("select follower from follows where followee = %s",(user['email'],))
			followee_follower = cursor.fetchall()
			cursor.execute("select thread from subscribes where user = %s",(user['email'],))
			subs = cursor.fetchall()
			user.update({
				'following': list(t[0] for t in follower_followee),
				'followers': list(t[0] for t in followee_follower),
				'subscriptions': list(t[0] for t in subs)
			})

		cursor.close()
		return jsonify(code=0, response=users)
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
	try:
		cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
		user = request.args['user']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_id = request.args.get('since_id', False)

		query = ""
		query_params = ()
		if since_id:
			query = """select about, email, users.id, isAnonymous, name, username from follows 
			join users on follows.followee = users.email and follows.follower = %s and users.id >= %s order by name """ + order
			query_params = (user, since_id, )
		else:
			query = """select about, email, users.id, isAnonymous, name, username from follows 
			join users on follows.followee = users.email and follows.follower = %s order by name """ + order
			query_params = (user,)

		if limit != '':
			query += " limit " + limit

		cursor.execute(query, query_params)
		users = cursor.fetchall()
		cursor = db.get_cursor()
		for user in users:
			cursor.execute("select followee from follows where follower = %s",(user['email'],))
			follower_followee = cursor.fetchall()
			cursor.execute("select follower from follows where followee = %s",(user['email'],))
			followee_follower = cursor.fetchall()
			cursor.execute("select thread from subscribes where user = %s",(user['email'],))
			subs = cursor.fetchall()
			user.update({
				'following': list(t[0] for t in follower_followee),
				'followers': list(t[0] for t in followee_follower),
				'subscriptions': list(t[0] for t in subs)
			})

		cursor.close()
		return jsonify(code=0, response=users)
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		name = data['name']
		user = data['user']
		about = data['about']
		cursor.execute("update users set name = %s, about = %s where email = %s",(name, about, user))
		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_user_info(user, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='user not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		user = request.args['user']
		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', False)

		query = ""
		query_params = ()
		if since_date:
			query = """select * from posts where user = %s and date >= %s order by date """ + order
			query_params = (user, since_date, )
		else: 
			query = """select * from posts where user = %s order by date """ + order
			query_params = (user,)
		
		if limit != '':
			query += " limit " + limit

		cursor.execute(query, query_params)
		posts = cursor.fetchall()
		for post in posts:
			post.update({"date": str(post["date"])})
		cursor.close()
		return jsonify(code=0, response=posts)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

""" THREADS """

@app.route('/db/api/thread/create/', methods=['POST'])
def thread_create():
	cursor = db.get_cursor()
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

		cursor.execute("""insert into threads (date, forum, isClosed, isDeleted,
					   message, slug, title, user) 	
				       values (%s, %s, %s, %s, %s,
				   	   %s, %s, %s)""",(date, forum, closed, deleted, message, slug, title, user))
		db.commit()
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
		return jsonify(code=0, response=get_thread_info(thread, db, related))
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		user = data['user']
		thread = data['thread']
		cursor.execute("insert into subscribes (user, thread) VALUES (%s, %s)",(user, thread))
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		user = data['user']
		thread = data['thread']
		cursor.execute("delete from subscribes where user = %s and thread = %s",(user, thread))
		db.commit()
		cursor.close()
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except:
		return jsonify(code=4, response='opps')
	return jsonify(code=0, 
				   response={"thread": thread, "user": user})

@app.route("/db/api/thread/update/", methods=['POST'])
def thread_update():
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		message = data['message']
		slug = data['slug']
		thread = data['thread']
		cursor.execute("update threads set message = %s, slug = %s where id = %s",(message, slug, thread))
		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_thread_info(thread, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/close/", methods=['POST'])
def thread_close():
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("update threads set isClosed = 1 where id = %s",(thread,))
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("update threads set isClosed = 0 where id = %s",(thread,))
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		thread = data['thread']
		cursor.execute("""update threads set isDeleted = 1, posts = 0 where id = %s""",(thread,))
		cursor.execute("""update posts set isDeleted = 1 where thread = %s""", (thread,))
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		thread = data['thread']
		count_posts = cursor.execute("""update posts set isDeleted = 0 where thread = %s""", (thread,))
		cursor.execute("""update threads set isDeleted = 0, posts = %s where id = %s""",(count_posts, thread,))
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		vote = data['vote']
		thread = data['thread']
		if vote == 1:
			cursor.execute("update threads set likes = likes + 1, points = points + 1 where id = %s",(thread,))
		else:
			cursor.execute("update threads set dislikes = dislikes + 1, points = points - 1 where id = %s",(thread,))

		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_thread_info(thread, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/thread/list/", methods=['GET'])
def thread_list():
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		user = request.args.get('user', False)
		forum = request.args.get('forum', False)

		if ((user and forum) or not (user or forum)): raise Exception('only one')

		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', False)


		query = ""
		query_params = ()
		if user:
			query = """select * from threads where user = %s """
			query_params = (user,)
		else:
			query = """select * from threads where forum = %s """
			query_params = (forum,)

		if since_date:
			query += "and date >= %s "
			query_params += (since_date,)
		query += "order by date " + order
		
		if limit != '':
			query += " limit " + limit
		
		cursor.execute(query, query_params)

		threads = cursor.fetchall()
		for thread in threads:
			thread.update({"date": str(thread["date"])})
		cursor.close()
		return jsonify(code=0, response=threads)
	
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
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		thread = request.args['thread']

		limit = request.args.get('limit', '')
		sort = request.args.get('sort', 'flat')
		order = request.args.get('order', 'desc')
		
		since_date = request.args.get('since', False)
		
		
		max_date = datetime.now()
		
		query = ""
		query_params = ()
		if sort == 'flat':
			query = """select * from posts where thread = %s """
			query_params += (thread,)
			if since_date:
				query += "and date >= %s "
				query_params += (since_date, )
			query += "order by date " + order

			if limit != '':
				query += " limit " + limit
			
		#elif sort == 'tree':
		#	query = """select p2.id from posts as p join posts as p2 on p2.mpath 
		#			like CONCAT(p.mpath,'%') and p.parent is null and thread = {} and createDate between '{}' and '{}'
		#			order by p.mpath {} {};""".format(thread, since_date, max_date, order, 
		#									   "limit {}".format(limit) if limit != '' else '')
		#else:
		#	query = """select p2.id from posts as p2 join 
		#	(select p.mpath, p.id from posts as p where parent is null {} ) as p 
		#	on p2.mpath like CONCAT(p.mpath,'%') and thread = {} and createDate between '{}' and '{}' 
		#	order by p.mpath {}""".format("limit {}".format(limit) if limit != '' else '',
		#							thread, since_date, max_date, order)
		
		cursor.execute(query, query_params)
		posts = cursor.fetchall()
		for post in posts:
			post.update({"date": str(post["date"])})
		cursor.close()
		return jsonify(code=0, response=posts)
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

""" POSTS """

@app.route('/db/api/post/create/', methods=['POST'])
def post_create():
	cursor = db.get_cursor()
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
		cursor.execute("""insert into posts (date, forum, isHighlighted, isApproved,
						isDeleted, isEdited, isSpam, message, parent, thread, user) 	
				   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)""",
				   (date, forum, isHighlighted, isApproved, isDeleted, isEdited, isSpam,
				   	message, parent, thread, user))

		lid = cursor.lastrowid
		cursor.execute("""update threads set posts = posts + 1 where id = (select thread from posts where id = %s)""",(lid,))
		if parent:
			cursor.execute("select mpath from posts where id = {}".format(parent))
			parent_mpath = cursor.fetchone()[0]+right_index(lid)
		else:
			parent_mpath = right_index(lid)
		cursor.execute("update posts set mpath = '{}/' where id = {}".format(parent_mpath,lid))
		cursor.close()

		db.commit()
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
	#		return jsonify(code=2, response=get_post_info(short_name, db))
	#	elif e[0] == 1452:
	#		return jsonify(code=2, response='user not found')
	#except:
	#	return jsonify(code=2, response='bad request')

@app.route("/db/api/post/details/", methods=['GET'])
def post_details():
	try:
		post = request.args['post']
		related = request.args.getlist('related')
		return jsonify(code=0, response=get_post_info(post, db, related))
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		post = data['post']
		cursor.execute("update posts set isDeleted = 1 where id = %s",(post,))
		cursor.execute("update threads set posts = posts - 1 where id = (select thread from posts where id = %s)", (post,))
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		post = data['post']
		cursor.execute("update posts set isDeleted = 0 where id = %s",(post,))
		cursor.execute("update threads set posts = posts + 1 where id = (select thread from posts where id = %s)", (post,))
		
		db.commit()
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
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		vote = data['vote']
		post = data['post']
		if vote == 1:
			cursor.execute("update posts set likes = likes + 1, points = points + 1 where id = %s",(post,))
		else:
			cursor.execute("update posts set dislikes = dislikes + 1, points = points - 1 where id = %s",(post,))

		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_post_info(post, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/update/", methods=['POST'])
def post_update():
	cursor = db.get_cursor()
	try:
		data = request.get_json()
		post = data['post']
		message = data['message']
		cursor.execute("update posts set message = %s where id = %s",(message, post))
		db.commit()
		cursor.close()
		return jsonify(code=0, 
				   response=get_post_info(post, db))
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except IntegrityError:
		return jsonify(code=1, response='not found')
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/post/list/", methods=['GET'])
def post_list():
	cursor = db.get_cursor(MySQLdb.cursors.DictCursor)
	try:
		thread = request.args.get('thread', False)
		forum = request.args.get('forum', False)

		if ((thread and forum) or not (thread or forum)): raise Exception('only one')

		limit = request.args.get('limit', '')
		order = request.args.get('order', 'desc')
		since_date = request.args.get('since', False)
	
		query = ""
		query_params = ()
		if thread:
			query = """select * from posts where thread = %s """
			query_params = (thread,)
		else:
			query = """select * from posts where forum = %s """
			query_params = (forum,)
		if since_date:
			query += "and date >= %s "
			query_params += (since_date, )
		query += " order by date " + order
		
		if limit != '':
			query += " limit " + limit

		cursor.execute(query, query_params)

		posts = cursor.fetchall()
		
		for post in posts:
			post.update({'date': str(post['date'])})

		cursor.close()
		return jsonify(code=0, response=posts)
	
	except KeyError:
		return jsonify(code=2, response='invalid json')
	except DoesNotExist:
		return jsonify(code=1, response='does not exist')
	except IntegrityError, e:
		return jsonify(code=1, response='something not found')
	except:
		return jsonify(code=4, response='opps')

@app.route('/db/api/clear/', methods=['POST'])
def clear():
	try:
		cursor = db.get_cursor()
		cursor.execute("""delete from users;""");
		db.commit()
		cursor.close()
		return jsonify(code=0, response="OK")
	except:
		return jsonify(code=4, response='opps')

@app.route("/db/api/status/", methods=['GET'])
def status():
	try:
		cursor = db.get_cursor()
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


@app.route("/")
def index():
	get_thread_info(63, db)
	return "lol"

if __name__ == '__main__':
	app.run()