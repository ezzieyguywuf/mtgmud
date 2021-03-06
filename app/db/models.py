from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column, Integer, String, Boolean, PickleType, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import config

engine = create_engine(config.DATABASE)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

USER_FLAGS = {
    'admin':False,
    'allow_spec': False,
    'banned': False,
    'muted': False,
    'frozen': False
}

def generate_password_hash(password):
    return pbkdf2_sha256.encrypt(password, rounds=150000, salt_size=15)

def check_password_hash(password, password_hash):
    return pbkdf2_sha256.verify(password, password_hash)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    aliases = Column(MutableDict.as_mutable(PickleType))
    flags = Column(MutableDict.as_mutable(PickleType), default=USER_FLAGS)
    decks = relationship('Deck')
    deck = relationship('Deck', uselist=False, back_populates='user')
    listening = Column(String)
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
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

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

    @staticmethod
    def search(card_name):
        return session.query(Card).filter(Card.name.like(card_name)).all()

    def __repr__(self):
        return "<Card(name='{}')>".format(self.name)


class Deck(Base):
    __tablename__ = 'decks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='deck')
    # cards is a dict() of { card.id: no_of_cards }
    cards = Column(MutableDict.as_mutable(PickleType))

    @property
    def no_cards(self):
        num = 0
        for card in self.cards:
            num += self.cards[card]
        return num

    def show(self):
        buff = "\nDeck: {}".format(self.name)
        for card in self.cards:
            buff += "\n{} x {}".format(self.cards[card], session.query(Card).get(card).name)
        return buff

    def __repr__(self):
        return "<Deck(name='{}')>".format(self.name)


class Channel(Base):
    __tablename__ = 'channels'

    key = Column(String(1), primary_key=True)
    name = Column(String)
    colour_token = Column(String(2))
    # Channel.types:
    # 0 - server
    # 1 - room
    # 2 - table
    # 3 - user (whisper)
    type = Column(Integer)
    default = Column(Boolean, default=False)


class Emote(Base):
    __tablename__ = 'emotes'
    id = Column(Integer, primary_key=True)
    name = Column(String(16))
    user_no_vict = Column(String(128))
    others_no_vict = Column(String(128))
    user_vict = Column(String(128))
    others_vict = Column(String(128))
    vict_vict = Column(String(128))
    user_vict_self = Column(String(128))
    others_vict_self = Column(String(128))

Base.metadata.create_all(engine)
