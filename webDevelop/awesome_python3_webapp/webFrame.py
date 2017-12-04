#before Web development,we need to make our own Web framework.
#Why we need to do that ? 
#in the vision of users, aiohttp is bottom， when we need to  
#write one URL handler func, need to follow some steps:
#1. write a handler() decorated to coroutine by 'async' 
#2. use 'request.match_info['xxx']' or 'request.query_string' to get parameter sent by browser 
#3. create Reponse func by your self. ex:
#text=render_templete('xxx.html')  
#return web.Response(text.encode('utf-8'))
#those duplicate work can be done by framework.
#One frame is for that users just need to write little code to complish 
#their job.
#so ,let's start!

import asyncio, os, inspect, logging, functools
from urllib import parse
from aiohttp import web
from apis import APIError

#define 'get' to map funcs to URL handler.
def get(path):
	'''
	define decorator @get('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrappers(*args,**kw):
			return func(*args,**kw)
		wrappers.__method__='GET'
		wrappers.__route__=path
		return wrappers
	return decorator

def post(path):
	'''
	define decorator @post('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrappers(*args,**kw):
			return func(*args,**kw)
		wrappers.__method__='POST'
		wrappers.__route__=path
		return wrappers
	return decorator

def get_required_kw_args(fn):
	args=[]
	params=inspect.signature(fn).parameters
	for name, param in params.items():
		if param.kind==inspect.Parameter.KEYWORD_ONLY and param.default==inspect.Parameter.empty:
			args.append(name)		
	return tuple(args)

def get_named_kw_args(fn):
	args=[]
	params=inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind==inspect.Parameter.KEYWORD_ONLY and param.default== inspect.Parameter.empty:
			args.append(name)
	return tuple(args)

def has_named_kw_args(fn):
	params=inspect.signature(fn).parameters
	for name, param in params.items():
		if param.kind==inspect.Parameter.KEYWORD_ONLY:
			return True

def has_var_kw_args(fn):
	params=inspect.signature(fn).parameters
	for name, param in params.items():
		if param.kind==inspect.Parameter.VAR_KEYWORD:
			return True

def has_request_kw_args(fn):
	sign=inspect.signature(fn)
	params=sign.parameters
	found=False
	for name, param in params.items():
		if name=='request':
			found= True
			continue
		if found and (param.kind!=inspect.Parameter.VAR_POSITIONAL and param.kind !=inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
			raise ValueError('request parameter must be the last named parameter in function: %s%s'%(fn.__name__,str(sign)))

	return found



#define 'RequestHandler' class
class RequestHandler(object):
	def  __init__(self,app,fn):
		self._app=app
		self._func=fn
		self._has_request_args=has_request_kw_args(fn)
		self._has_var_kw_args=has_var_kw_args(fn)
		self._has_named_kw_args=has_named_kw_args(fn)
		self._named_kw_args=get_named_kw_args(fn)
		self._required_kw_args=get_required_kw_args(fn)



	#make 'RequestHandler' instance can act as one func
	async def __call__(self,request):
		kw=None
		if self._has_var_kw_args or self._has_named_kw_args or self._required_kw_args:
			if request.method=='POST':
				if not request.content_type:
					return web.HTTPBadRequest(text='Missing Content-Type.')
				ct=request.content_type.lower()
				logging.info('show content-type of request: %s'%ct)
				if ct.startswith('application/json'):
					params=await request.json()
					logging.info('show params: %s'%params)
					if not isinstance(params,dict):
						return web.HTTPBadRequest(text='JSON body must be object.')
					kw=params
				elif ct.startswith('applicaton/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
					params=await request.post()
					kw=dict(**params)
				else:
					return web.HTTPBadRequest(text='Unsupported content-type: %s.'%request.content_type)

			if request.method=='GET':
				qs=request.query_string
				logging.info('query_string: %s'%qs)
				if qs:
					kw=dict()
					for k,v in parse.parse_qs(qs, True).items():
						kw[k]=v[0]

		if kw is None:
			kw=dict(**request.match_info)
		else:
			if not self._has_var_kw_args and self._named_kw_args:
				#remove all unnamed kw
				copy=dict()
				for name in self._named_kw_args:
					if name in kw:
						copy[name]=kw[name]
				kw=copy
			#check named arg
			for k,v in request.match_info.items():
				if k in kw:
					logging.warning('Duplicate arg name in named arg and kw args:%s'%k)
				kw[k]=v
		if self._has_request_args:
			kw['request']=request
		#check required kw:
		if self._required_kw_args:
			for name in self._required_kw_args:
				if not (name in kw):
					return web.HTTPBadRequest(text='Missing argument: %s'%name)
					
		logging.info('call with args: %s'%str(kw))
		try:
			r= await self._func(**kw)
			return r
		except:
			raise APIError('Invalid')



def add_static(app):
	path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
	app.router.add_static('/static/',path)
	logging.info('add static %s->%s'%('/static/',path))


	#define 'add_route' to register URL handler

def add_route(app,fn):
	method=getattr(fn,'__method__',None)
	path=getattr(fn,'__route__',None)
	if path is None or method is None:
		raise ValueError('@get or @post not define in %s.'%str(fn))
	if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
		fn=asyncio.coroutine(fn)

	logging.info('add route %s  %s-->%s(%s)'%(method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
	app.router.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,module_name):
	n=module_name.rfind('.')
	if n==(-1):
		mod=__import__(module_name,globals(),locals())
	else:
		name=module_name[n+1:]
		mod=getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
	for attr in dir(mod):
		if attr.startswith('_'):
			continue
		fn=getattr(mod,attr)
		if callable(fn):
			method=getattr(fn,'__method__',None)
			path=getattr(fn,'__route__',None)
			if method and path:
				add_route(app,fn)