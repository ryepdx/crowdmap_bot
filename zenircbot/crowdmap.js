var api = require('zenircbot-api');
var zen = new api.ZenIRCBot();
var sub = zen.get_redis_client();

zen.register_commands("crowdmap.js",
     [{name: "!crowdmap <tweetid>",
      description: "Pushes given tweet into ushahidi."
    }]);

sub.subscribe('in');
sub.on('message', function(channel, message) {
  console.log(message)
    var msg = JSON.parse(message);
    var sender = msg.data.sender;
    if (msg.version == 1) {
      var match = /crowdmap(\s+(.*))?/i.exec(msg.data.message);
      var extra = match[2]
      if(extra)
        var ematch = /(\d+)(.*)?/.exec(extra)
        if(ematch.length > 0) {
          var tweetid = ematch[1]
          zen.send_privmsg(msg.data.channel,
                        sender + ': tweet #' + tweetid);
        } else {
          zen.send_privmsg(msg.data.channel,
                        sender + ': help');

        }
      }
    });
