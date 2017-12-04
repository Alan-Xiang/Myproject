#coding=utf-8

#ORM is 'object relationship mapping', it maps one row of
#database to a object, that means 'one class one table'.
#if we do this, code will be simple, and don't need to use
#SQL.Creaing the ORM frame, all class need dynamic defination, 
#because only user know constructure , and define the class
#
#write bottom model, first we need to write application interface
#
#
#First define 'Model' as basic class of mapping for all ORM

import logging;logging.basicConfig(level=logging.INFO)
import asyncio,aiomysql

def log(sql,args=()):
	logging.info('sql:%s'%sql)

#all data(log/user info/comment) is stored in database,
#if we want to get data, it's necessary to establish database access
#create database access pool
#each HTTP request can get database access from this pool,
#the benefit of using pool is that we don't need to open/close
#database access frequently

async def create_pool(loop,**kw):
	logging.info('Create database access pool')
	global __pool
	__pool=await aiomysql.create_pool(
		host=kw.get('host','localhost'),
		port=kw.get('port',3306),
		user=kw['user'],
		password=kw['password'],
		db=kw['db'],
		charset=kw.get('charset','utf8'),
		


		autocommit=kw.get('autocommit','True'),
		maxsize=kw.get('maxsize',10),
		minsize=kw.get('minsize',1),
		loop=loop
	)


#define some primary operation:select/insert/update/delete
#'select' will return info set, and others return affected
#rows. SQL use "?" as placeholder,but "%s" in MySQL, so we  
#need do exchange internally. It is batter to use SQL with 
#parameter to prevent SQL  attack.



async def select(sql,args,size=None):
	log(sql,args)
	global __pool
	with (await __pool) as conn:
		cur=await conn.cursor(aiomysql.DictCursor)
		await cur.execute(sql.replace('?','%s'),args or ())
		if size:
			rs=await cur.fetchmany(size)
		else:
			rs=await cur.fetchall()
		await cur.close()
		logging.info('row return:%s'%len(rs))
		return rs

async def execute(sql,args):
	log(sql)
	with (await __pool) as conn:
		try:
			cur=await conn.cursor(aiomysql.DictCursor)
			await cur.execute(sql.replace('?','%s'),args)
			affected=cur.rowcount
			await cur.close()
		except BaseException as a:
			raise 
		return affected

def create_args_string(num):
	j=[]
	while num>0:
		j.append('?')
		num=num-1
	return ','.join(j)


#define 'Field',contain name / column_type / primary_key / default  

class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name=name
		self.column_type=column_type
		self.primary_key=primary_key
		self.default=default

	def __str__(self):
		return '<%s,%s:%s>'% (self.__class__.__name__,self.column_type,self.name)

class StringField(Field):
	def __init__(self,name=None,primary_key=False,default=None):
		super(StringField,self).__init__(name,'varchar(100)',primary_key,default)

class IntegerField(Field):
	def __init__(self, name=None,primary_key=False,default=0):
		super(IntegerField,self).__init__(name,'bigint',primary_key,default)

class BooleanField(Field):
	def  __init__(self,name=None,primary_key=False,default=False):
		super(BooleanField,self).__init__(name,'boolean',primary_key,default)

class FloatField(Field):
	def __init__(self,name=None,primary_key=False,default=0.0):
		super(FloatField,self).__init__(name,'real',primary_key,default)


class TextField(Field):
	def __init__(self,name=None,primary_key=False,default=None):
		super(TextField,self).__init__(name,'text',primary_key,default)


#write ModelMetaclass, dynamic Creaing class, 
#complete mapping relationsehip

class ModelMetaclass(type):
	def __new__(cls,name,bases,attrs):
		
		#except 'Model', not for itself  
		if name=='Model':
			return type.__new__(cls,name,bases,attrs)

		#get name of table
		tableName=attrs.get('__table__',None) or name
		logging.info('found model:%s(table:%s)'%(name,tableName))
		#get all field and primaryKey
		fields=[]
		primaryKey=None
		mappings=dict()
		for k,v in attrs.items():
			if isinstance(v,Field):
				logging.info('Found mapping:%s-->%s'%(k,v))
				mappings[k]=v
				if v.primary_key:
				#find the main key
					if primaryKey:
						raise RuntimeError('Duplicate primary key for Fields: %s'%k)
					primaryKey=k
				else:
					fields.append(k)
		if not primaryKey:
			raise RuntimeError('primary Key not found.')
		for k in mappings.keys():
			attrs.pop(k)

		escaped_fields=list(map(lambda f:'`%s`'%f,fields))
		attrs['__mappings__']=mappings  #store the mapping relationship between attrs and column
		attrs['__table__']=tableName
		attrs['__primary_key__']=primaryKey  #store main key attr name
		attrs['__fields__']=fields  #store non-main key attr name
		attrs['__insert__']='insert into `%s` (%s,`%s`) values(%s)'%(tableName,','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1)) 
		attrs['__select__']='select `%s` ,%s from `%s`'%(primaryKey,','.join(escaped_fields),tableName)
		attrs['__update__']='update `%s` set %s where `%s`=?' %(tableName,','.join(map(lambda f:'`%s`=?'%(mappings.get(f).name or f),fields)),primaryKey)
		attrs['__delete__']='delete from `%s` where `%s`=?'%(tableName,primaryKey)

		return type.__new__(cls,name,bases,attrs)


		
		

#create base class-Model
class Model(dict,metaclass=ModelMetaclass):
	
	def __init__(self,**kw):
		super(Model,self).__init__(**kw)

	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'"%key)

	def __setattr__(self,key,value):
		self[key]=value

	def getValue(self,key):
		return getattr(self,key,None)

	def getValueOrDefault(self,key):
		value=getattr(self,key,None)
		if value is None:
			field=self.__mappings__[key]
			if field.default is not None:
				value=field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s:%s'%(key,str(value)))
				setattr(self,key,value)
		return value

	#add class method
	@classmethod
	async def find(cls,pk):
		'find object by primary Key'
		rs=await select('%s where `%s`=?'%(cls.__select__,cls.__primary_key__),[pk],1)
		if len(rs)==0:
			return None
		return cls(**rs[0])

	@classmethod
	async def findAll(cls,where=None,args=None,**kw):
		'find object by where clasue.'
		sql=[cls.__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args=[]
		orderBy=kw.get('orderBy',None)
		if orderBy:
			sql.append('order By')
			sql.append(orderBy)
		limit=kw.get('limit',None)
		if limit is not None:
			sql.append('limit')
			if isinstance(limit,int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit,tuple) and len(limit)==2:
				sql.append('?, ?')
				args.extend(limit)
			else:
				raise ValueError('Invalid limit value:%s'%str(limit))
		rs=await select(' '.join(sql),args)
		return [cls(**r) for r in rs]

	@classmethod
	async def findNumber(cls, selectField, where=None, args=None):
		'find number by select and where'
		sql=['select %s _num_ from `%s`'%(selectField, cls.__table__)]
		if  where:
			sql.append('where')
			sql.append(where)
		rs=await select(' '.join(sql),args,1)
		if len(rs)==0:
			return None
		return rs[0]['_num_']


	#write save method
	async def save(self):
		args=list(map(self.getValueOrDefault,self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows=await execute(self.__insert__, args)
		if rows !=1:
			logging.warn('failed to insert recored:affected row %s'%rows)

	async def update(self):
		args=list(map(self.getValue, self.__fields__))
		args.append(self.getValue(self.__primary_key__))
		rows=await execute(self.__update__, args)
		if rows !=1:
			logging.warn('failed to update by primary key : affected rows: %s'% rows)

	async def remove(self):
		args=[self.getValue(self.__primary_key__)]
		rows= await execute(self.__delete__, args)
		if rows != 1:
			logging.info('failed to remove by primary Key : affected rows:%s'%rows)