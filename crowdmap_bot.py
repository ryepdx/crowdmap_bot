import unittest
import time, requests, json
from datetime import datetime, timedelta
from email.utils import parsedate_tz
from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers
from settings import IRC_HOST, BOT_NICK, BOT_CHANNEL, \
BOT_PASS, MAP_API, PARENT_CATEGORY_ID

class MsgHandler(DefaultCommandHandler):
    
    def __init__(self, *args, **kwargs):
        self.crowdmap = CrowdMap(MAP_API, PARENT_CATEGORY_ID)
        super(MsgHandler, self).__init__(*args, **kwargs)
    
    def privmsg(self, nick, chan, msg):
        msg_parts = msg.split(":")
        
        if (chan == BOT_CHANNEL and len(msg_parts) > 0 
        and msg_parts[0] == BOT_NICK):
            command = msg_parts[1].strip()
            
            # Show the available categories.
            if command == 'categories':
                for key in sorted(self.crowdmap.categories):
                    helpers.msg(self.client, chan, "%s. %s" % (key,
                        self.crowdmap.categories[key]))
                
            # Add a pin to the map.
            else:
                commands = command.split(' ')
                tags = []
                tweet_id = commands[0]
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
            
                self.crowdmap.add_tweet(Twitter.get_tweet(tweet_id),
                    tags, ' '.join(commands[(command_index-1):]))


class GoogleMap:
    @staticmethod
    def get_geocode(address):
        return json.loads(
            requests.get('https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address=%s'
                % address).text)
    
class Twitter:
    @staticmethod
    def get_tweet(id):
        return json.loads(
            requests.get('https://api.twitter.com/1/statuses/show.json?id=%s'
                % id).text)
    
    @staticmethod
    def to_datetime(datestring):
        time_tuple = parsedate_tz(datestring.strip())
        dt = datetime(*time_tuple[:6])
        return dt - timedelta(seconds=time_tuple[-1])

class CrowdMap:

    def __init__(self, map_api, parent_category = None):
        self.map_api = map_api
        self.categories = self.get_categories(parent_category)
    
    def get_map_params(self, tweet, tags, neighborhood, coords):
        params = {}
        date = Twitter.to_datetime(tweet['created_at'])
        
        params['incident_title'] = tweet['text'][0:50] + '...'
        params['incident_description'] = tweet['text']
        params['incident_date'] = date.strftime('%m/%d/%Y')
        params['incident_hour'] = date.strftime('%I')
        params['incident_minute'] = date.strftime('%M')
        params['incident_ampm'] = date.strftime('%p')
        params['incident_category'] = ','.join(tags)
        params['latitude'] = coords['lat']
        params['longitude'] = coords['lng']
        params['location_name'] = neighborhood
        
        return params

    def add_tweet(self, tweet, tags, address=''):
        coords = None

        if address != '':
            geo = GoogleMap.get_geocode(address)

        elif 'geo' in tweet and 'coordinates' in tweet['geo']:
            coords = tweet['geo']['coordinates']
            geo = GoogleMap.get_geocode('%s,%s' % (coords[0], coords[1]))
            
        # If we obtained a geocode for this tweet, put it on the map.
        if geo['status'] == 'OK' and len(geo['results']) > 0:
            geo = geo['results'][0]
            neighborhood = [component['long_name']
                        for component in geo['address_components']
                            if 'political' in component['types']][0]
                            
            return requests.post('http://%s?task=report' % MAP_API,
                data=self.get_map_params(tweet, tags,
                neighborhood, geo['geometry']['location']))
        else:
            return None

    def get_categories(self, parent_id = None):
        response = json.loads(requests.get('https://%s?task=categories'
            % self.map_api).text)
        
        return dict([(cat['category']['id'], cat['category']['title'])
            for cat in response['payload']['categories']
                if parent_id == None or cat['category']['parent_id'] == parent_id])


class CrowdMapBot:
    
    def __init__(self, host, nick, passwd, channel, port=6667):
        self.host = host
        self.port = port
        self.nick = nick
        self.passwd = passwd
        self.channel = channel
        self.running = True
    
    def connect(self):
        cli = IRCClient(MsgHandler, host=self.host, port=self.port,
            nick=self.nick, connect_cb=self.on_connect)
        conn = cli.connect()

        while self.running:
            conn.next()
            
    def on_connect(self, cli):
        # Identify to nickserv
        helpers.identify(cli, self.passwd)

        # Join the channel
        helpers.join(cli, self.channel)

class TestCrowdMap(unittest.TestCase):
    """
    Simple tests for the CrowdMap class.
    You can run them with: python -m unittest crowdmap_bot
    """
    def setUp(self):
        self._map = CrowdMap('sandyaiddev.crowdmap.com/api')
        self.categories = {u'1': u'Category 1', u'3': u'Category 3',
             u'2': u'Category 2', u'4': u'Trusted Reports'}
        
    def test_categories(self):
        self.assertEqual(self._map.categories, self.categories)
             
    def test_get_categories(self):
        self.assertEqual(self._map.get_categories(), self.categories)

def main():
    bot = CrowdMapBot(IRC_HOST, BOT_NICK, BOT_PASS, BOT_CHANNEL)
    bot.connect()

if __name__ == "__main__":
    main()
