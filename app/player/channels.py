from app import server

# Non-User channels
def do_action(client, msg_self, msg_others):
    for c in client.user.table.clients:
        if c is client:
            client.msg_client(c, "\n[ACT] You {}".format(msg_self))
        else:
            client.msg_client(c, "\n[ACT] {} {}".format(client.user.name, msg_others))

# User channels
def do_chat(client, msg):
    for c in server.clients:
        if c.user is not None:
            if c is client:
                client.msg_client(c, "\n[chat] You: {}".format(msg))
            else:
                client.msg_client(c, "\n[chat] {}: {}".format(client.user.name, msg))

def do_say(client, msg):
    for user in client.user.room.occupants:
        c = server.get_client(user)
        if c is client:
            client.msg_client(c, "\n[say] You: {}".format(msg))
        else:
            client.msg_client(c, "\n[say] {}: {}".format(client.user.name, msg))

def do_tchat(client, msg):
    for c in client.user.table.clients:
        if c is client:
            client.msg_client(c, "\n[table] You: {}".format(msg))
        else:
            client.msg_client(c, "\n[table] {} : {}".format(client.user.name, msg))

def do_whisper(client, msg):
    args = msg.split()
    recip = args[0]
    msg = ' '.join(args[1:])
    recip = server.get_client(recip)
    if recip is None:
        client.msg_self("\nCould not find user {}.".format(args[0]))
        return
    client.msg_client(client, "\n[whisper] You: {}".format(msg))
    client.msg_client(recip, "\n[whisper] {}: {}".format(client.user.name, msg))


channels = {
    '.':  do_chat,
    '\'': do_say,
    ':': do_tchat,
    '>':  do_whisper
}