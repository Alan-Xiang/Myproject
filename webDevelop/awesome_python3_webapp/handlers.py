#-*-coding=utf-8-*-

__author__='Alan Xiang'

'url handlers'

import re,time,json,logging,hashlib,base64,asyncio
from webFrame import *
from model import User,Blog,Comment,next_id

@get('/')
def index(request):
	summary='Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
	blogs=[
		Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
		Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
		Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
	]
	return {
		'__template__' : 'blogs.html',
		'blogs' : blogs
	} 

#Web API: If the return of one URL is not HTML but data which machine can read directly,
#we call this URL as Web API. 
#the advantage of API is API can package all Web App function, so operate data by API 
#can separate front-end code from back-end code. 
#One API is also one URL handler, so we create one API to catch sign-in users info.
#
@get('/api/users')
async def api_get__users():
	users=await User.findAll()
	for u in users:
		u.password='******'
	return dict(users=users)


