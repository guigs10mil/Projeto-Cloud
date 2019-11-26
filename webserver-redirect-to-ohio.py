from fastapi import FastAPI
from enum import Enum
from pydantic import BaseModel
import requests
import json
import re
import os


class Contact(BaseModel):
    firstName: str
    lastName: str
    email: str = ''
    company: str = ''
    phone: int = 0


app = FastAPI()

ip = os.getenv('mongodbWebserverIp')

@app.get("/")
async def root():
    return {"msg": "Hello World"}

@app.get("/healthcheck/")
async def healthcheck():
    a = requests.get(url = 'http://' + ip +':3000/healthcheck')
    return a.json()

@app.get("/contact/")
async def get_contacts():
    a = requests.get(url = 'http://' + ip +':3000/contact')
    return a.json()

@app.post("/contact/")
async def post_contact(contact: Contact):
    data = {
        "firstName": contact.firstName, 
        "lastName": contact.lastName}
    a = requests.post(url = 'http://' + ip +':3000/contact', data = data)
    return a.json()

@app.get("/contact/{id}")
async def get_contact(id: str):
    a = requests.get(url = 'http://' + ip +':3000/contact/' + id)
    return a.json()

@app.put("/contact/{id}")
async def put_contact(id: str, contact: Contact):
    data = {
        "firstName": contact.firstName, 
        "lastName": contact.lastName}
    a = requests.put(url = 'http://' + ip +':3000/contact/' + id, data = data)
    return a.json()

@app.delete("/contact/{id}")
async def delete_contact(id: str):
    a = requests.delete(url = 'http://' + ip +':3000/contact/' + id)
    return a.json()
