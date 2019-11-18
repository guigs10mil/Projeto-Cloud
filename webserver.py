from fastapi import FastAPI
from enum import Enum
from pydantic import BaseModel
import json
import re


class Tarefa(BaseModel):
    title: str
    done: bool

tarefas = {}


app = FastAPI()

@app.get("/")
async def root():
    return {"msg": "Hello World"}

@app.get("/healthcheck/")
async def healthcheck():
    return {"msg": "Ok"}

@app.get("/Tarefa/")
async def get_tarefas():
    return tarefas

@app.post("/Tarefa/")
async def post_tarefa(tarefa: Tarefa):
    if len(tarefas) > 0:
        id_counter = list(tarefas)[-1] + 1
    else:
        id_counter = 0
    tarefas[id_counter] = {'title': tarefa.title, 'done': tarefa.done}
    return {"msg": "Tarefa posted"}

@app.get("/Tarefa/{id}")
async def get_tarefa(id: int):
    return tarefas[id]

@app.put("/Tarefa/{id}")
async def put_tarefa(id: int, tarefa: Tarefa):
    tarefas[id] = {'title': tarefa.title, 'done': tarefa.done}
    return {"msg": "Tarefa putted"}

@app.delete("/Tarefa/{id}")
async def delete_tarefa(id: int):
    del tarefas[id]
    return {"msg": "Tarefa deleted"}