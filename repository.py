import sqlite3
from pydantic import BaseModel
from datetime import datetime

class OrderItem(BaseModel):
    id: int | None = None
    order_id: int | None = None
    name: str
    quantity: int
    price: float

class Order(BaseModel):
    id: int | None = None
    customer_name: str
    total: int
    task_id: str | None = None
    order_items: list[OrderItem] = []
    created_at: datetime | None = None

class OrderItemRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.initialize_db()

    def initialize_db(self):
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                name TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        self.db.commit()

    def _map_order_item(self, row):
        return OrderItem(
            id=row[0],
            order_id=row[1],
            name=row[2],
            quantity=row[3],
            price=row[4]
        )

    def get_order_items(self, order_id):
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,))
        rows = cursor.fetchall()
        order_items = list(map(self._map_order_item, rows))
        return order_items
    
    def add_order_item(self, order_item: OrderItem):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO order_items (order_id, name, quantity, price) VALUES (?, ?, ?, ?)', (order_item.order_id, order_item.name, order_item.quantity, order_item.price))
        self.db.commit()
        order_item.id = cursor.lastrowid
        return order_item
    
    def update_order_item(self, order_item: OrderItem):
        cursor = self.db.cursor()
        cursor.execute('UPDATE order_items SET name = ?, quantity = ?, price = ? WHERE id = ?', (order_item.name, order_item.quantity, order_item.price, order_item.id))
        self.db.commit()

class OrdersRepository:
    def __init__(self):
        self.db = sqlite3.connect('orders.db')
        self.initialize_db()
        self.order_items_repo = OrderItemRepository(self.db)

    def initialize_db(self):
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_name TEXT,
                total REAL,
                task_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db.commit()

    def _map_order(self, row):
        return Order(
            id=row[0],
            customer_name=row[1],
            total=row[2],
            task_id=row[3],
            created_at=row[4]
        )

    def get_orders(self):
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        rows = cursor.fetchall()
        orders = []
        for row in rows:
            order = self._map_order(row)
            order.order_items = self.order_items_repo.get_order_items(order.id)
            orders.append(order)
        return orders

    def get_order(self, order_id):
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        order = self._map_order(row)
        order.order_items = self.order_items_repo.get_order_items(order.id)
        return order

    def add_order(self, order: Order):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO orders (customer_name, total) VALUES (?, ?)', (order.customer_name, order.total))
        self.db.commit()
        order.id = cursor.lastrowid
        for item in order.order_items:
            item.order_id = order.id
            self.order_items_repo.add_order_item(item)
        return order

    def update_order(self, order: Order):
        cursor = self.db.cursor()
        cursor.execute('UPDATE orders SET customer_name = ?, total = ?, task_id = ? WHERE id = ?', (order.customer_name, order.total, order.task_id, order.id))
        self.db.commit()

        for item in order.order_items:
            if item.id is None:
                item.order_id = order.id
                self.order_items_repo.add_order_item(item)
            else:
                self.order_items_repo.update_order_item(item)

    def delete_order(self, order_id):
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
        self.db.commit()

class MunchkinsRepository:
    def get_munchkins():
        return [
            {"name": "Choco Munchkin", "price": 10, "wait_time": 3},
            {"name": "Butternut Munchkin", "price": 15, "wait_time": 2},
            {"name": "Choco Butternut Munchkin", "price": 20, "wait_time": 2},
            {"name": "Choco Honey Dip Munchkin", "price": 25, "wait_time": 2},
            {"name": "Choco Honey Dip Butternut Munchkin", "price": 30, "wait_time": 3},
            {"name": "Choco Honey Dip Butternut Munchkin with Almonds", "price": 35, "wait_time": 5},
            {"name": "Matcha Munchkin", "price": 90, "wait_time": 3},
        ]
    
    def get_munchkin(self, name: str):
        munchkins = MunchkinsRepository.get_munchkins()
        for munchkin in munchkins:
            if munchkin['name'] == name:
                return munchkin
        return None