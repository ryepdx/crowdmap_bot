import requests, json
from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers
from settings import BOT_NICK, BOT_CHANNEL, BOT_PASS

def on_connect(cli):
    # Identify to nickserv
    helpers.identify(cli, BOT_PASS)

    # Join the channel '#test'
    helpers.join(cli, BOT_CHANNEL)

class MsgHandler(DefaultCommandHandler):
    
    def privmsg(self, nick, chan, msg):
        msg_parts = msg.split(":")
        
        if (chan == BOT_CHANNEL and len(msg_parts) > 0 
        and msg_parts[0] == BOT_NICK):
            commands = msg_parts[1].strip().split(' ')
            tags = []
            tweet_id = commands[1]
            commands = commands[1:]
            
            command_index = 0
            in_tags = True
            while in_tags and command_index < len(commands):
                command = commands[command_index]
                if command[0] == '#':
                    tags.append(command[1:])
                else:
                    in_tags = False
                command_index += 1
            
            address = ' '.join(commands[(command_index-1):])
            
            # Pass on the address, tags, and tweet ID.
            tweet = get_tweet(tweet_id)
            

def get_tweet(id):
    return json.loads(
        requests.get('https://api.twitter.com/1/statuses/show.json?id=%s'
            % id))['text']

cli = IRCClient(MsgHandler, host="niven.freenode.net", port=6667,
    nick=BOT_NICK, connect_cb=on_connect)

conn = cli.connect()
while True:
    conn.next()
