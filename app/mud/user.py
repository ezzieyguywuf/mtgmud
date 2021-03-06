from asyncio import Protocol

from app import db, server, config
from app.player import actions, channels
from app.style import colourify

class User(Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.addr = transport.get_extra_info('peername')
        self.authd = False
        self.name = None
        self.admin = False
        self.room = None
        self.table = None
        self.db = None

        self.flags = []

        print("Connected: {}".format(self.addr))
        server.connected.append(self)

        actions['help'](self, ['welcome'])
        self.get_prompt()

    def data_received(self, data):
        msg = data.decode().strip()
        args = msg.split()

        if self.authd is False:
            actions['login'](self, args)
            return

        if msg:

            if args[0] in self.db.aliases:
                args[0] = str(self.db.aliases[args[0]])
                msg = ' '.join(args)
                args = msg.split()

            if msg[0] in server.channels:
                ch = db.session.query(db.models.Channel).get(msg[0])
                if msg[1] =='@':
                    channels.send_to_channel(self, ch, msg[2:], do_emote=True)
                else:
                    channels.send_to_channel(self, ch, msg[1:])
                self.get_prompt()
                return

            if args[0] in actions:
                if self.is_frozen():
                    self.send_to_self("You're frozen solid!")
                else:
                    actions[args[0]](self, args[1:] if len(args) > 1 else None)
                self.get_prompt()
                return
            self.send_to_self("Huh?")
        else:
            if self.table is not None:
                actions['table'](self, None)
            elif self.room is not None:
                actions['look'](self, None)

        self.get_prompt()

    def get_prompt(self):
        buff = ""
        if self.name is not None:
            buff += "&B<&x &c{}&x ".format(self.name)
            if self.deck is not None:
                buff += "&B||&x &c{}&x &C(&x&c{}&x&C)&x ".format(self.deck.name, self.deck.no_cards)
            if self.table is not None:
                buff += "&B||&x &GH&x:&G{}&x &YL&x:&Y{}&x &yG&x:&y{}&x ".format(len(self.table.hands[self]), len(self.table.libraries[self]), len(self.table.graveyards[self]))
        buff += "&B>&x&w>> &x"
        self.send_to_self(buff)

    def send_to_self(self, msg):
        msg = "\r\n" + msg
        msg = colourify(msg)
        self.transport.write(msg.encode())

    @staticmethod
    def send_to_user(user, msg):
        msg = "\r\n"+msg
        msg = colourify(msg)
        user.transport.write(msg.encode())

    @staticmethod
    def send_to_users(users, msg):
        msg = "\r\n"+msg
        msg = colourify(msg)
        for user in users:
            user.transport.write(msg.encode())

    def is_admin(self):
        return self.flags['admin']

    def is_muted(self):
        return self.flags['muted']

    def is_frozen(self):
        return self.flags['frozen']

    def is_banned(self):
        return self.flags['banned']

    def can_spectate(self):
        return self.flags['allow_spec']

    def load(self, dbUser):
        for user in server.users:
            if user.db.id is dbUser.id:
                self.send_to_user(user, "You have signed in from another location!")
                actions['quit'](user, None)
        self.authd = True
        self.name = str(dbUser.name)
        self.flags = dict(dbUser.flags)
        self.deck = dbUser.deck
        self.decks = dbUser.decks
        self.db = dbUser
        server.users.append(self)
        lobby = server.get_room(config.LOBBY_ROOM_NAME)
        self.room = lobby
        lobby.occupants.append(self)

        if self.name == config.ADMIN and not self.is_admin():
            self.flags['admin'] = True
            self.save()

    def save(self):
        self.db.name = self.name
        self.db.flags = self.flags
        db.session.commit()

    def connection_lost(self, ex):
        print("Disconnected: {}".format(self.addr))
        server.connected.remove(self)
        
        if self.authd:
            self.save()
            server.users.remove(self)
            self.room.occupants.remove(self)

