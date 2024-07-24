from mongoengine import connect

def db_connect():
    connect(db="zeroci")
