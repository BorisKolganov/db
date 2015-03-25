class DoesNotExist(Exception):
	pass
		
def get_user_info(user_email, connection):
	cursor = connection.cursor()
	if cursor.execute("select * from Users where email = '{}'".format(user_email)) == 0:
		raise DoesNotExist
	user = cursor.fetchone()
	cursor.execute("select followee from follows where follower = '{}'".format(user[3]))
	follower_followee = cursor.fetchall()
	cursor.execute("select follower from follows where followee = '{}'".format(user[3]))
	followee_follower = cursor.fetchall()
	cursor.execute("select thread from subscribes where userEmail = '{}'".format(user[3]))
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

def get_forum_info(forum_sname, connection, related=[]):
	cursor = connection.cursor()
	if cursor.execute("select * from forums where shortname = '{}'".format(forum_sname)) == 0:
		raise DoesNotExist
	forum = cursor.fetchone()
	cursor.close()
	return {'id': forum[0],
			'name': forum[1],
			'short_name': forum[2],
			'user': forum[4] if 'user' not in related else get_user_info(forum[4], connection)}

def get_thread_info(thread_id, connection, related=[]):
	cursor = connection.cursor()
	if cursor.execute("select * from threads where id = {}".format(thread_id)) == 0:
		raise DoesNotExist
	thread = cursor.fetchone()
	cursor.close()
	return { "date": thread[1].strftime("%Y-%m-%d %H:%M:%S"),
		     "dislikes": thread[10],
		     "forum": thread[2] if 'forum' not in related else get_forum_info(thread[2], connection),
		     "id": thread[0],
		     "isClosed": bool(thread[3]),
		     "isDeleted": bool(thread[4]),
		     "likes":thread[9],
		     "message": thread[5],
		     "points": thread[9]-thread[10],
		     "posts":thread[11],# if not bool(thread[4]) else 0, 
		     "slug": thread[6],
		     "title": thread[7],
		     "user": thread[8] if 'user' not in related else get_user_info(thread[8], connection)
	}

def get_post_info(post_id, connection, related=[]):
	cursor = connection.cursor()
	if cursor.execute("select * from posts where id = {}".format(post_id)) == 0:
		raise DoesNotExist
	post = cursor.fetchone()
	cursor.close()
	return { "date": post[1].strftime("%Y-%m-%d %H:%M:%S"),
        "dislikes": post[13],
        "forum": post[2] if 'forum' not in related else get_forum_info(post[2], connection),
        "id": post[0],
        "isApproved": bool(post[4]),
        "isDeleted": bool(post[5]),
        "isEdited": bool(post[6]),
        "isHighlighted": bool(post[3]),
        "isSpam": bool(post[7]),
        "likes": post[12],
        "message": post[8],
        "parent": post[9],
        "points": post[12]-post[13],
        "thread": post[10] if 'thread' not in related else get_thread_info(post[10],connection),
        "user": post[11] if 'user' not in related else get_user_info(post[11], connection)
    }


def right_index(index):
	len = 1000000000 + index
	return str(len)[1:]
