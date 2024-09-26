# for taskiq
import taskiq_fastapi
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

# for tasks
import asyncio
from repository import Order, MunchkinsRepository

REDIS_URL = 'redis://localhost:6379/0'

broker = ListQueueBroker(REDIS_URL).with_result_backend(
    RedisAsyncResultBackend(REDIS_URL)
)

@broker.task
async def prepare_order(order: Order):
    munchkins_repo = MunchkinsRepository()
    
    if len(order.order_items) == 0:
        return {'status': 'ERROR', 'message': 'Order has no items'}

    for order_item in order.order_items:
        munchkin = munchkins_repo.get_munchkin(order_item.name)
        print(munchkin)
        if munchkin is None:
            return {'status': 'ERROR', 'message': f'Munchkin {order_item.name} not found'}
        
        print(f'munchkin: {munchkin}')
        await asyncio.sleep(munchkin['wait_time'] * order_item.quantity)

    return {
        'status': 'READY'
    }