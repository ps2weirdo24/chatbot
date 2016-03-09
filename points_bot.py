#!/usr/bin/env python
#Username = DrunkandSuch
#Password = ps2weirdo24
#AppName = mychatbot
#Redirect URL = http://www.ryangaudy.pythonanywhere.com
#Client ID = b69qxr73yp8w2qzndu0uf33kfcg4ej7
#Client Secret = k52i0txi4yznjvgs8wi4a40gb8xfaij
#Oauth = oauth:3kf2n0z24rg5ghttypstftudjt2huk

# Username elmagnificobot
# Pass ps2weirdo24
# Client ID dvddixl07tdgner32kxn02m1z9dybpn
# Client Secret q1fpco46rbgv9jnr0ldmw2u61jf81h9
# oath oauth:89i2gcrqdo6eo237hrbqmdufh5ubcd


# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import json
import time, sys
import threading
from datetime import date, datetime, timedelta

listofmods = ["elmagnificobot", "elmagnificotaco", "drunkandsuch", "rawandsuch", "ggjeffles"]

NICKNAME = "elmagnificobot"
PASSWORD = "oauth:89i2gcrqdo6eo237hrbqmdufh5ubcd"

class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, myfile):
        self.file = myfile
        
    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""
    nickname = NICKNAME
    password = PASSWORD

    def connectionMade(self):
    	self.jfilename = "player_points.json"
    	self.interval_players = []
    	loadfile = open(self.jfilename, 'r')
    	self.player_points = json.load(loadfile)
    	loadfile.close()
    	self.commands = ["!mypoints", "!allpoints", "!store"]
    	intervals = threading.Thread(target=self.do_interval)
    	intervals.start()
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        if not self.factory.silent_console:
            print "Connected!"

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        self.logger.close()
        if not self.factory.silent_console:
            print "Disconnected!"

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        if not self.factory.silent_console:
            print "Signed on to the server!"

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))
        if msg.split(" ")[0] in self.commands:
        	self.docommand(channel, user.lower(), str(msg))
        if not user.lower() in self.interval_players:
        	self.interval_players.append(str(user.lower()))
        if not self.factory.silent_console:
            print (user, msg) 

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    def interval(self, points):
    	for item in self.interval_players:
    		if item in self.player_points.keys():
    			self.player_points[item] += int(points)
    		else:
    			self.player_points[item] = int(points)
    	self.interval_players = []
    	self.jfile = open(self.jfilename, 'w')
    	json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
    	self.jfile.close()
    	print "Points Awarded!"

    def do_interval(self):
    	while True:
    		time.sleep(300)
    		self.interval(5)
    def docommand(self, channel, user, message):
    	this_command = str(message)
    	this_user = str(user)
    	if this_command == "!mypoints":
    		if not this_user in self.player_points.keys():
    			str_send = "Sorry %s you haven't earned any points just yet, keep watching and commenting to recieve points" % (this_user)
    			self.msg(channel, str_send)
    		else:
    			this_points = str(self.player_points[this_user])
    			str_send = "%s's points: %s" % (this_user, this_points)
    			self.msg(channel, str_send)
    	
    	elif this_command == "!allpoints":
    		this_msg = str(self.player_points)
    		self.msg(channel, this_msg)




class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel, filename, silent_console):
        self.channel = channel
        self.filename = filename
        self.silent_console = silent_console

    def buildProtocol(self, addr):
        p = LogBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        if not self.factory.silent_console:
            print "connection failed:", reason
        reactor.stop()


class ChatCollector:

    def __init__(self, channel, output_filename, seconds_runtime, silent_console=False):

        if channel.startswith("#"):
            self.channel = channel
        else:
            self.channel = "#" + channel
        self.outfile = output_filename
        self.timer = int(seconds_runtime)
        self.silent_console = silent_console

        if not self.silent_console:
            log.startLogging(sys.stdout)
        else:
            pass
        bot_instance = LogBotFactory(self.channel, self.outfile, self.silent_console)
        reactor.connectTCP("irc.twitch.tv", 6667, bot_instance)

    def start(self):
        ircsuicide = threading.Timer(self.timer, reactor.stop)
        ircsuicide.start()
        reactor.run()
    def start_forever(self):
        reactor.run()

if __name__ == "__main__":
    mybot = ChatCollector("elmagnificotaco", "tacolog.txt", 1800, silent_console=False)
    mybot.start_forever()