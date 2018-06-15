#!/usr/bin/env python



# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys
import threading
from datetime import date, datetime, timedelta
import json

print("LIST BOT")

options_file = open("options.json", "r")
loaded_options = json.load(options_file)
options_file.close()

#listofmods = ["elmagnificobot", "elmagnificotaco", "drunkandsuch", "rawandsuch", "ggjeffles"]
listofmods = list(loaded_options["options"]["listofmods"])
#globself.listofplayers = ["testplayer1", "testplayer2", "testplayer3"]

NICKNAME = str(loaded_options["options"]["nickname"])
PASSWORD = str(loaded_options["options"]["password"])

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
        self.listofplayers = []
        recoverfile = open("safetyfile.txt", "r")
        for item in recoverfile.readlines():
            to_add = str(item)[0:(len(item)-1)] 
            self.listofplayers.append(to_add)
        print "Crashed but recovered %s" % (str(self.listofplayers))
        self.list_open = True
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
        if user.lower() in listofmods:
            if msg == "!list":
                if len(self.listofplayers) == 0:
                    self.msg(channel, "The list of players is currently empty, type !join to join it! ElTaco")
                else:
                    count_index = 1
                    msgtosend = ""
                    for item in self.listofplayers:
                        msg = "%s. %s " % (str(count_index), str(item))
                        count_index = count_index + 1
                        msgtosend = msgtosend + msg
                    self.msg(channel, str(msgtosend[:-1]))
            elif "!remove" in msg:
                toremove = msg.split(" ")[1].lower()
                if toremove in self.listofplayers:
                    self.listofplayers.remove(toremove)
                    self.msg(channel, toremove + " has been removed from the list. ElRip")
            elif msg == "!clearlist":
                self.listofplayers = []
                self.msg(channel, "The list of players has been cleared. ElRip")
            elif msg == "!next":
                if len(self.listofplayers) <= 1:
                    pass
                else:
                    removed = str(self.listofplayers[0])
                    up_next = str(self.listofplayers[1]) 
                    self.listofplayers = self.listofplayers[1:]
                    msg_to_send = "GG %s, %s takes his place! Good luck, have fun! ElTaken" % (removed, up_next)
                    self.msg(channel, msg_to_send)
            elif msg == "!help":
                helpmsg = "To join the playing list use '!join', to leave the playing list use '!leave' and to show the current playing list use '!list'. ElTaco"
                self.msg(channel, str(helpmsg))
            elif msg == "!join":
                if (str(user)).lower() in self.listofplayers:
                    print "idk"
                else:
                    if self.list_open:
                        self.listofplayers.append((str(user)).lower())
                        self.msg(channel, str(user).lower() + " has been added. ElTacoHi")
                    elif (not self.list_open):
                        themsg = "Sorry " + user + " but the list is currently closed. ElRip"
                        self.msg(channel, themsg)
                    else:
                        pass
            elif msg == "!leave":
                if (str(user)).lower() in self.listofplayers:
                    self.listofplayers.remove((str(user)).lower())
                    self.msg(channel, str(user).lower() + " has left the list. ElRip")
                else:
                    pass

            elif msg == "!openlist":
                if not self.list_open:
                    self.list_open = True
                    self.msg(channel, "The list has now been opened, type !join to join the list!. ElTacoHi")
            elif msg == "!closelist":
                if self.list_open:
                    self.list_open = False
                    self.msg(channel, "The list has now been closed, the !join command is now disabled. ElRip")
                else:
                    pass
        else:
            if msg == "!list":
                if len(self.listofplayers) == 0:
                    self.msg(channel, "The list of players is currently empty, type !join to join it! ElTaco")
                else:
                    count_index = 1
                    msgtosend = ""
                    for item in self.listofplayers:
                        msg = "%s. %s " % (str(count_index), str(item))
                        count_index = count_index + 1
                        msgtosend = msgtosend + msg
                    self.msg(channel, str(msgtosend[:-1]))
            elif msg == "!join":
                if (str(user)).lower() in self.listofplayers:
                    print "idk"
                else:
                    if self.list_open:
                        self.listofplayers.append((str(user)).lower())
                        self.msg(channel, str(user).lower() + " has been added.")
                    elif not self.list_open:
                        themsg = "Sorry " + user + " but the list is currently closed. ElRip"
                        self.msg(channel, themsg)
            elif msg == "!leave":
                if (str(user)).lower() in self.listofplayers:
                    self.listofplayers.remove((str(user)).lower())
                    self.msg(channel, str(user).lower() + " has left the list. ElRip")
                else:
                    pass
            elif msg == "!help":
                helpmsg = "To join the playing list use '!join', to leave the playing list use '!leave' and to show the current playing list use '!list'. ElTaco"
                self.msg(channel, str(helpmsg))
        if not self.factory.silent_console:
            print (user, msg)
        safetyfile = open("safetyfile.txt", "w")
        for item in self.listofplayers:
            safetyfile.write(item + "\n")
        safetyfile.close()

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))


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
    mybot = ChatCollector(str(loaded_options["options"]["channel"]), str(loaded_options["options"]["log_file_name"]), 1800, silent_console=False)
    mybot.start_forever()
