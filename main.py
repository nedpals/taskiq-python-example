from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from taskiq_config import broker, prepare_order
from repository import Order, OrdersRepository, MunchkinsRepository
import os

SERVER_PORT = int(os.getenv('SERVER_PORT', '8000'))

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):    
    if not broker.is_worker_process:
        print('Starting broker')
        await broker.startup()
    
    yield

    if not broker.is_worker_process:
        print('Shutting down broker')
        await broker.shutdown()

@app.get("/")
async def home(req: Request):
    return templates.TemplateResponse(req, "index.html")

@app.get("/munchkins")
async def munchkins_list():
    return MunchkinsRepository.get_munchkins()

@app.post("/orders")
async def new_order(order: Order, req: Request):
    orders_repo = OrdersRepository()
    orders_repo.add_order(order)

    task = await prepare_order.kiq(order)
    order.task_id = task.task_id

    orders_repo.update_order(order)
    orders_repo.db.close()

    return {
        "type": "success",
        "message": "Order created successfully!",
        "order": order
    }

@app.get("/orders")
async def get_orders():
    orders_repo = OrdersRepository()
    orders = orders_repo.get_orders()
    orders_repo.db.close()
    return orders

@app.get("/order_status/{task_id}")
async def order_status(task_id: str):
    is_result_ready = await broker.result_backend.is_result_ready(task_id)
    if not is_result_ready:
        return {'status': 'PENDING'}
    
    task_result = await broker.result_backend.get_result(task_id)
    if not task_result.return_value:
        return {'status': 'UNKNOWN'}

    return task_result.return_value

@app.delete("/claim_order/{order_id}")
async def claim_order(order_id: int):
    orders_repo = OrdersRepository()
    orders_repo.delete_order(order_id)

    return {
        "type": "success",
        "message": "Order claimed successfully!",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=SERVER_PORT, reload=True, log_level="debug")