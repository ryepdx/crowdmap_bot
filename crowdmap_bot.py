import time, requests, json
from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers
from settings import BOT_NICK, BOT_CHANNEL, BOT_PASS, MAP_API

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
            
            # Get the tweet and the geocode.
            tweet = get_tweet(tweet_id)
            coords = None

            if address != '':
                geo = get_geocode(address)

            elif 'geo' in tweet and 'coordinates' in tweet['geo']:
                coords = tweet['geo']['coordinates']
                geo = get_geocode('%s,%s' % (coords[0], coords[1]))
            
            # If we obtained a geocode for this tweet, put it on the map.
            if geo['status'] == 'OK' and len(geo['results']) > 0:
                geo = geo['results'][0]
                neighborhood = [x['long_name']
                                for x in geo['address_components']
                                    if 'political' in x['types']][0]
                add_to_map(tweet['text'], tags, neighborhood, geo['geometry']['location'])

def get_tweet(id):
    return json.loads(
        requests.get('https://api.twitter.com/1/statuses/show.json?id=%s'
            % id))

def get_geocode(address):
    return json.loads(
        requests.get('https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address=%s'
            % address))

def get_map_params(tweet, tags, neighborhood, coords):
    params = {}
    date = time.strptime(tweet['created_at'], '%a, %d %b %Y %H:%M:%S')
    
    params['incident_title'] = tweet['text'][0:50] + '...'
    params['incident_description'] = tweet['text']
    params['incident_date'] = time.strftime('%m/%d/%Y', date)
    params['incident_hour'] = time.strftime('%I', date)
    params['incident_minute'] = time.strftime('%M', date)
    params['incident_ampm'] = time.strftime('%p', date)
    params['incident_category'] = 0
    params['latitude'] = coords['lat']
    params['longitude'] = coords['lng']
    params['location_name'] = neighborhood 

def add_to_map(text, tags, coords):
    return requests.post(

cli = IRCClient(MsgHandler, host="irc.freenode.net", port=6667,
    nick=BOT_NICK, connect_cb=on_connect)

conn = cli.connect()
while True:
    conn.next()
