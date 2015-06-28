import MySQLdb

class DoesNotExist(Exception):
	pass

class DB():
	def __init__(self):
		self.connection = MySQLdb.connect(host="localhost", user="root", db="db_api")
		#self.get_cursor().execute("SET FOREIGN_KEY_CHECKS = 0;");
	def get_cursor(self, modif=None):
		self.connection.ping(True)
		return self.connection.cursor(modif)
	def commit(self):
		self.connection.commit()



def get_forum_info(forum_sname, db, related=[]):
	cursor = db.get_cursor()
	if cursor.execute("select * from forums where shortname = %s",(forum_sname,)) == 0:
		raise DoesNotExist
	forum = cursor.fetchone()
	cursor.close()
	return {'id': forum[0],
			'name': forum[1],
			'short_name': forum[2],
			'user': forum[4] if 'user' not in related else get_user_info(forum[4], db)}


def get_user_info(user_email, db):
	cursor = db.get_cursor()
	if cursor.execute("select * from users where email = %s",(user_email,)) == 0:
		raise DoesNotExist
	user = cursor.fetchone()
	cursor.execute("select followee from follows where follower = %s",(user[3],))
	follower_followee = cursor.fetchall()
	cursor.execute("select follower from follows where followee = %s",(user[3],))
	followee_follower = cursor.fetchall()
	cursor.execute("select thread from subscribes where user = %s",(user[3],))
	subs = cursor.fetchall()
	cursor.close()
	return {'id':user[0],
			'name': user[1],
			'username': user[2],
			'email': user[3],
			'about':user[4],
			'isAnonymous':bool(user[5]),
			'following': list(t[0] for t in follower_followee),
			'followers': list(t[0] for t in followee_follower),
			'subscriptions': list(t[0] for t in subs)}

def get_thread_info(thread_id, db, related=[]):
	cursor = db.get_cursor()
	if cursor.execute("select * from threads where id = %s", (thread_id,)) == 0:
		raise DoesNotExist
	thread = cursor.fetchone()
	cursor.close()
	return { "date": thread[1].strftime("%Y-%m-%d %H:%M:%S"),
		     "dislikes": thread[10],
		     "forum": thread[2] if 'forum' not in related else get_forum_info(thread[2], db),
		     "id": thread[0],
		     "isClosed": bool(thread[3]),
		     "isDeleted": bool(thread[4]),
		     "likes":thread[9],
		     "message": thread[5],
		     "points": thread[11],
		     "posts":thread[12],
		     "slug": thread[6],
		     "title": thread[7],
		     "user": thread[8] if 'user' not in related else get_user_info(thread[8], db)
	}

def get_post_info(post_id, db, related=[]):
	cursor = db.get_cursor()
	if cursor.execute("select * from posts where id = {}".format(post_id)) == 0:
		raise DoesNotExist
	post = cursor.fetchone()
	cursor.close()
	return { "date": str(post[1]),
        "dislikes": post[13],
        "forum": post[2] if 'forum' not in related else get_forum_info(post[2], db),
        "id": post[0],
        "isApproved": bool(post[4]),
        "isDeleted": bool(post[5]),
        "isEdited": bool(post[6]),
        "isHighlighted": bool(post[3]),
        "isSpam": bool(post[7]),
        "likes": post[12],
        "message": post[8],
        "parent": post[9],
        "points": post[14],
        "thread": post[10] if 'thread' not in related else get_thread_info(post[10],db),
        "user": post[11] if 'user' not in related else get_user_info(post[11],db)
    }

def right_index(index):
	len = 1000000000 + index
	return str(len)[1:]
