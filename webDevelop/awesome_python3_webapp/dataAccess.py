import orm
import asyncio
from model import User,Blog,Comment

async def test(loop):
	await orm.create_pool(loop,user='www-data',password='www-data',db='awesome')
	u=User(name='Test',email='test@qq.com',password='123456',image='about:blank')
	await u.save()

loop=asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
