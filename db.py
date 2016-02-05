import os
import json
from passlib.hash import pbkdf2_sha256
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.environ.get('DATABASE') or 'sqlite:///' + os.path.join(basedir, 'database.sqlite')

engine = create_engine(DATABASE)
Session = sessionmaker(bind=engine)

Base = declarative_base()

def generate_password_hash(password):
    return pbkdf2_sha256.encrypt(password, rounds=150000, salt_size=15)

def check_password_hash(password, password_hash):
    return pbkdf2_sha256.verify(password, password_hash)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    room = None
    _decks = Column(String)
    _password = Column(String)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(password, self._password)

    @property
    def decks(self):
        return self.decks

    @decks.setter
    def set_decks(self, d):
        self.decks = json.dumps(d)

    @decks.getter
    def get_decks(self):
        return json.loads(self.decks)

    def add_deck(self, deck):
        self.decks.append(deck)


    def __repr__(self):
        return "<User(username='{}')>".format(self.username)


class Room(Base):
    __tablename__ = 'tables'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    occupants = []

    def look(self):
        buff = "[{}]\n{}\n".format(self.name, self.description)
        buff += "# " + ", ".join([client.user.name for client in self.occupants])
        return buff


    def __repr__(self):
        return "<Room(name='{}', description='{}')>".format(self.name, self.description)

Base.metadata.create_all(engine)