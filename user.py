class User():
	def __init__(connection):
		self.cursor = connection.cursor()
	def add(user):
	try:
		name = user['name']
		username = user['username']
		email = user['email']
		about = user['about']
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
							 "isAnonymous":isAnonymous,
							 "about":about
							})
	except KeyError:
		return jsonify(code=3, response='invalid json')
	except IntegrityError:
		return jsonify(code=5,response='user alredy exist')
	except:
		return jsonify(code=2, response='bad request')
