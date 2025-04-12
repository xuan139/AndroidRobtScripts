#!/bin/bash

# 创建 FastAPI 示例应用
echo "Creating a basic FastAPI app with CRUD APIs..."
cat <<EOL > main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# 数据模型
class Item(BaseModel):
    name: str
    description: str
    price: float
    on_sale: bool

# 模拟数据库
fake_db: Dict[int, Item] = {}
item_id_counter = 1

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

# Create (POST)
@app.post("/items/")
def create_item(item: Item):
    global item_id_counter
    fake_db[item_id_counter] = item
    item_id_counter += 1
    return {"id": item_id_counter - 1, "data": item}

# Read (GET)
@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "data": fake_db[item_id]}

# Update (PUT)
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    fake_db[item_id] = item
    return {"id": item_id, "data": item}

# Delete (DELETE)
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del fake_db[item_id]
    return {"message": f"Item {item_id} deleted successfully"}
EOL

echo "FastAPI app with CRUD APIs created in main.py!"

