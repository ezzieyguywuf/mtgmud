import os
import json
from passlib.hash import pbkdf2_sha256
from sqlalchemy import create_engine, Column, Integer, String, PickleType, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.environ.get('DATABASE') or 'sqlite:///' + os.path.join(basedir, 'database.sqlite')

engine = create_engine(DATABASE)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


def generate_password_hash(password):
    return pbkdf2_sha256.encrypt(password, rounds=150000, salt_size=15)


def check_password_hash(password, password_hash):
    return pbkdf2_sha256.verify(password, password_hash)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    admin = Column(String, default=False)
    room = None
    table = None
    decks = relationship('Deck')
    deck = None
    deck_id = Column(Integer)
    _password = Column(String)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(password, self._password)

    def __repr__(self):
        return "<User(username='{}')>".format(self.username)


class Room(Base):
    __tablename__ = 'tables'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    occupants = []

    def look(self):
        buff = "\n[{}]\n{}".format(self.name, self.description)
        buff += "\n# " + ", ".join([client.user.name for client in self.occupants])
        return buff

    def __repr__(self):
        return "<Room(name='{}', description='{}')>".format(self.name, self.description)


class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True)

    name = Column(String, index=True)
    names = Column(PickleType)
    manaCost = Column(String)
    cmc = Column(Integer)
    colors = Column(PickleType)
    type = Column(String)
    supertypes = Column(PickleType)
    types = Column(PickleType)
    subtypes = Column(PickleType)
    rarity = Column(String)
    text = Column(String)
    power = Column(String)
    toughness = Column(String)
    loyalty = Column(String)

    def __repr__(self):
        return "<Card(name='{}')>".format(self.name)


class Deck(Base):
    __tablename__ = 'decks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))
    # cards is a dict() of { card.id: no_of_cards }
    cards = Column(PickleType)

    @property
    def no_cards(self):
        num = 0
        for card in self.cards:
            num += self.cards[card]
        return num

    def get(self):
        buff = []
        for card in self.cards:
            s_card = session.query(Card).get(card)
            for c in self.cards[card]:
                buff.append(s_card)
        return buff

    def show(self):
        buff = "\nDeck: {}".format(self.name)
        for card in self.cards:
            buff += "\n{} x {}".format(self.cards[card], session.query(Card).get(card).name)
        return buff

    def __repr__(self):
        return "<Deck(name='{}')>".format(self.name)


Base.metadata.create_all(engine)
