#day-4
#Now, we had ORM, so let's create 3 tables
#by Model
import time,uuid

from orm import Model ,StringField,BooleanField,FloatField,TextField

#use uuid4 to create one random ID
def next_id():
	return '%s000' % uuid.uuid4().hex


#Now we can create one simple ORM.
#ORM design need the vision of up-level application.
#First, we create 'User' class, and tie it to 
#database.

#tips:__table__/id/name is attribute of class,not instance.
#Those attributes characterize the mapping between User  object and table.
#The attribute of instance need __init__() to do initialization, so 
#it can't raise conflict.
class User(Model):
	__table__='users'

	id=StringField(primary_key=True,default=next_id)
	email=StringField()
	passwd=StringField()
	admin=BooleanField()
	name=StringField()
	image=StringField()
	created_at=FloatField(default=time.time)

class Blog(Model):
	__table__='blogs'

	id=StringField(primary_key=True,default=next_id)
	user_id=StringField()
	user_name=StringField()
	user_image=StringField()
	name=StringField()
	summary=StringField()
	content=TextField()
	created_at=FloatField(default=time.time)

class Comment(Model):
	__table__='Comments'

	id=StringField(primary_key=True,default=next_id)
	blog_id=StringField()
	user_id=StringField()
	user_name=StringField()
	user_image=StringField()
	content=TextField()
	created_at=FloatField(default=time.time)

#initial tables of database
#manually create SQL script of table


