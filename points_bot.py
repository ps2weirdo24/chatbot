#!/usr/bin/env python

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import json
import time, sys
import threading
from datetime import date, datetime, timedelta
import random
import os

# my own imports
import requests
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()
"""
Taco command > Bot announces bet is starting > X minutes to place bets >
betting ends, bot announces end and odds > Taco command for winner > 
bot announces winner and deals with points

(mod command)!startbet <betname1> <betname2> 
!bet <betname> <number of points>
!winner <betname>

thedict = {"betname1":{"player1": intbet,...},"betname2":{...}}

================ store formatting ===========

Taco Sticker - price is 5000 points, to buy one type '!buy sticker' / $10 Nintendo

"""

print("POINTS BOT")


options_file = open("options.json", "r")
loaded_options = json.load(options_file)
options_file.close()

listofmods = list(loaded_options["options"]["listofmods"])

list_of_active_commands = []

for item in loaded_options["active_commands"]:
    if loaded_options["active_commands"][str(item)]:
        list_of_active_commands.append(str(item))
    else:
        pass

#print(list_of_active_commands)
#listofmods = ["elmagnificobot", "elmagnificotaco", "drunkandsuch"]

NICKNAME = str(loaded_options["options"]["nickname"])
PASSWORD = str(loaded_options["options"]["password"])

the_store = dict(loaded_options["store"])

# create order file if not found and format it
this_order_file = "orders.txt"
if this_order_file in os.listdir(os.getcwd()):
    pass
else:
    thefile = open(this_order_file, "a")
    thefile.write("================ Orders ================\n")
    thefile.close()

client_id = str(loaded_options["options"]["client_id"])
head = {"client-id": client_id}


class FollowHandler():
    """
    A class that handles pulling follower data from the Twitch.tv API
    """
    def __init__(self, channel):
        self.this_channel = str(channel)
        self.og_url = "https://api.twitch.tv/kraken/channels/%s/follows?direction=DESC&limit=100" % (self.this_channel)
        self.filename = "follower_data.json"
        self.total_follow = self.get_total()
        self.current_list = self.get_list()
        self.check_new()

    def get_total(self):
        total_url = "https://api.twitch.tv/kraken/channels/%s/follows?direction=DESC&limit=1" % (self.this_channel)
        response = requests.get(total_url,headers=head)
        the_total = int(response.json()["_total"])
        return the_total

    def get_list(self):
        temp_open = open(self.filename,"r")
        to_return = json.load(temp_open)
        temp_open.close()
        return to_return

    def save_to_file(self):
        temp_open = open(self.filename,"w")
        json.dump(self.current_list, temp_open,indent=4)
        temp_open.close()

    def check_new(self):
        to_return = []
        url = self.og_url
        pulled_follow = []
        crit = True
        while crit:
            thisone = requests.get(url, headers=head)
            working_dict = thisone.json()
            if working_dict["follows"] == []:
                crit = False
            else:
                for item in working_dict["follows"]:
                    this_user = item["user"]["name"]
                    pulled_follow.append(this_user)
                    url = working_dict["_links"]["next"]
        for item in pulled_follow:
            if item not in self.current_list:
                to_return.append(item)
                self.current_list.append(item)
            else:
                pass
        self.save_to_file()
        return to_return


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
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.is_raffle_active = False
        self.amount_for_raffle = 0
        self.raffle_list = []
        #followers
        self.channel = "#elmagnificotaco"
        self.follow_handle = FollowHandler("elmagnificotaco")
        follow_thread = threading.Thread(target=self.follower_check)
        follow_thread.start()
        #followers
        #orders
        self.orderfile = this_order_file
        #orders
        #betting
        self.betname1 = ""
        self.betname2 = ""
        self.is_bet_active = False
        self.is_taking_bets = False
        self.betting_dict = {}
        #betting
        self.jfilename = "player_points.json"
        self.interval_players = []
        self.gamble_players = []
        loadfile = open(self.jfilename, 'r')
        self.player_points = json.load(loadfile)
        loadfile.close()
        """self.commands = ["!mypoints", "!allpoints", "!store", "!gamble",
                         "!award", "!startbet", "!bet", "!winner", "!buy",
                         "!take", "!startraffle", "!raffle", "!endraffle"]"""
        self.commands = list_of_active_commands
        intervals = threading.Thread(target=self.do_interval)
        intervals.start()
        gamble_intervals = threading.Thread(target=self.do_gamble_interval)
        gamble_intervals.start()
        #irc.IRCClient.connectionMade(self)
        #self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        if not self.factory.silent_console:
            print("Connected!")

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        self.logger.close()
        if not self.factory.silent_console:
            print("Disconnected!")

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        if not self.factory.silent_console:
            print("Signed on to the server!")

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
        print("Points Awarded!")

    def do_interval(self):
        while True:
            time.sleep(300)
            self.interval(5)

    def follower_check(self):
        while True:
            new_ones = self.follow_handle.check_new()
            if new_ones == []:
                pass
            else:
                for item in new_ones:
                    to_send = "We got a new follower! Thanks %s for the follow!" % (str(item))
                    self.msg(self.channel, to_send)
                    #print "FOLLOW"
            time.sleep(30)

    def end_taking_bets(self, channel, betname1, betname2):
        self.is_taking_bets = False
        to_send = "Betting has ended for %s vs %s, points will be distributed once a winner is announced!" % (str(betname1), str(betname2))
        self.msg(channel, to_send)

    def gamble_interval(self):
        self.gamble_players = []

    def do_gamble_interval(self):
        while True:
            time.sleep(300)
            print("Gamble timeout reset now!")
            self.gamble_interval()

    def docommand(self, channel, user, message):
        this_command = str(message)
        this_user = str(user).lower()
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
        
        elif this_command.split(" ")[0] == "!gamble":
            if len(this_command.split(" ")) == 2:
                crit = True
                nums = ["1","2","3","4","5","6","7","8","9","0"]
                for item in str(this_command.split(" ")[1]):
                    if not item in nums:
                        crit = False
                if crit:
                    self.gamble(channel, this_user, this_command)
        elif (this_command.split(" ")[0] == "!award") and (this_user in listofmods):
            if len(this_command.split(" ")) == 3:
                _, awarduser, num_points = this_command.split(" ")
                awarduser = awarduser.lower()
                if awarduser in self.player_points.keys():
                    self.player_points[awarduser] = self.player_points[awarduser] + int(num_points)
                elif not awarduser in self.player_points.keys():
                    self.player_points[awarduser] = int(num_points)
                msg_to_send = "Congratulations %s, you have recieved %s points from %s! Type !mypoints to see your new point balance." % (awarduser, str(num_points), this_user)
                self.msg(channel, msg_to_send)
            self.jfile = open(self.jfilename, 'w')
            json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
            self.jfile.close()
        elif (this_command.split(" ")[0] == "!take") and (this_user in listofmods):
            if len(this_command.split(" ")) == 3:
                _, awarduser, num_points = this_command.split(" ")
                awarduser = awarduser.lower()
                if (awarduser in self.player_points.keys()) and (self.player_points[awarduser] >= int(num_points)):
                    self.player_points[awarduser] = self.player_points[awarduser] - int(num_points)
                    to_send = "Sorry %s, you have had %s taken away by %s. Type !mypoints to see your new point balance." % (awarduser, str(num_points), this_user)
                    self.msg(channel, to_send)
                else:
                    to_send = "The user '%s' was either not found in the database or does not have %s points." % (awarduser, str(num_points))
                    self.msg(channel, to_send)
                self.jfile = open(self.jfilename, 'w')
                json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
                self.jfile.close()

        elif (this_command.split(" ")[0] == "!startbet") and (this_user in listofmods):
            if (len(this_command.split(" ")) == 3) and (not self.is_bet_active):
                self.betname1 = this_command.split(" ")[1].lower()
                self.betname2 = this_command.split(" ")[2].lower()
                self.is_bet_active = True
                self.betting_dict[self.betname1] = {}
                self.betting_dict[self.betname2] = {}
                self.is_taking_bets = True
                accept_bets = threading.Timer(120, self.end_taking_bets, args=[channel,self.betname1,self.betname2]) 
                accept_bets.start()
                this_warning = "30 seconds left to bet for either '%s' or '%s'!" % (self.betname1, self.betname2)
                warning_message = threading.Timer(90, self.msg, args=[channel, this_warning])
                warning_message.start()
                to_send = "Betting has begun for %s vs %s, type '!bet <%s or %s> <amount of points>' to place a bet!" % (self.betname1, self.betname2, self.betname1, self.betname2)
                self.msg(channel, to_send)
        elif this_command.split(" ")[0] == "!bet" and self.is_taking_bets:
            if this_user in self.player_points and len(this_command.split(" ")) == 3:
                if (this_user not in self.betting_dict[self.betname1].keys()) and (this_user not in self.betting_dict[self.betname2].keys()):
                    bet_amount = int(this_command.split(" ")[2])
                    thisbetname = str(this_command.split(" ")[1]).lower()
                    if self.player_points[this_user] >= bet_amount and bet_amount >= 10:
                        if thisbetname in self.betting_dict.keys():
                            self.betting_dict[thisbetname][this_user] = bet_amount
                            self.player_points[this_user] = self.player_points[this_user] - bet_amount
                            to_send = "%s has placed a bet of %s points on '%s'" % (this_user, str(bet_amount), thisbetname)
                            self.msg(channel, to_send)
                            self.jfile = open(self.jfilename, 'w')
                            json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
                            self.jfile.close()
                        else:
                            to_send = "Sorry, %s '%s' is not an option for the current bet. Current options are %s or %s" % (this_user, str(thisbetname), self.betname1, self.betname2)
                            self.msg(channel, to_send)
                    else:
                        to_send = "Sorry, %s you don't have that many points or have tried to bet less than the minimum bet (10 points)" % (str(this_user))
                        self.msg(channel, to_send)
                else:
                    to_send = "Sorry %s you have already placed a bet" % (this_user)
                    self.msg(channel, to_send)
        elif this_command.split(" ")[0] == "!winner" and this_user in listofmods:
            if (self.is_bet_active) and (len(this_command.split(" ")) == 2):
                betname_winner = this_command.split(" ")[1].lower()
                if betname_winner in self.betting_dict.keys():
                    self.handleWinner(channel, betname_winner)
                else:
                    to_send = "The winner %s was not one of the valid options for this bet, try '%s' or '%s'" % (betname_winner, self.betname1, self.betname2)
                    self.msg(channel, to_send)
        elif this_command.lower() == "!store":
            """
            Taco Sticker - price is 5000 points, to buy one type '!buy sticker' / $10 Nintendo
            """
            final_to_send = ""
            final_count = len(the_store)
            this_counter = 1
            for item in the_store:
                the_name = the_store[item]["name"]
                price = the_store[item]["price"]
                to_add = "%s - price is %s points, to buy one type '!buy %s'" % (str(the_name), str(price), str(item))
                if this_counter < final_count:
                    to_add = to_add + " / "
                this_counter = this_counter + 1
                final_to_send = final_to_send + to_add
            self.msg(channel, final_to_send)
        elif (this_command.split(" ")[0] == "!buy") and (len(this_command.split(" ")) == 2):
            to_buy = this_command.split(" ")[1]
            if str(to_buy) in the_store.keys():
                self.handlePurchase(channel, this_user, this_command)
            else:
                to_send = "Sorry, %s '%s' is not in the store, try typing '!store' to view the current store." % (str(this_user), str(to_buy))
                self.msg(channel, to_send)
        elif (this_command.split(" ")[0] == "!startraffle") and (this_user in listofmods):
        	amount_for_one = int(this_command.split(" ")[1])
        	self.start_raffle(channel, amount_for_one)
        elif (this_command.split(" ")[0] == "!endraffle") and (this_user in listofmods):
        	if self.is_raffle_active:
        		self.end_raffle(channel)
        	else:
        		to_send = "There are no active raffles."
        elif (this_command.split(" ")[0] == "!raffle") and (this_user in self.player_points.keys()):
        	if (len(this_command.split(" ")) == 2) and (self.player_points[this_user] >= float(this_command.split(" ")[1])):
        		self.do_raffle(channel, this_user, int(this_command.split(" ")[1]))


    def end_raffle(self, channel):
    	amount_of_people = len(self.raffle_list)
    	winning_number = random.randint(0, (amount_of_people - 1))
    	winner = self.raffle_list[winning_number]
    	to_send = "Congratulations %s, you won the raffle!" % (str(winner))
    	self.msg(channel, to_send)
    	self.is_raffle_active = False

    def do_raffle(self, channel, this_user, tickets):
    	amount_to_pay = float(tickets) * self.amount_for_raffle  
    	if (tickets % 1 != 0):
    		to_send = "Sorry %s but you must use whole numbers when buying tickets" % (str(this_user))
    		self.msg(channel, to_send)
    	elif (amount_to_pay > self.player_points[this_user]):
    		to_send = "Sorry, %s but you don't have enough points to buy those tickets. Try using '!mypoints' to view your points." % (str(this_user))
    		self.msg(channel, to_send)
    	else:
    		self.player_points[this_user] = self.player_points[this_user] - int(amount_to_pay)
    		to_send = "Thanks %s, you now have %s more chances to win the raffle" % (this_user, str(tickets))
    		self.msg(channel, to_send)
    		for item in range(tickets):
    			self.raffle_list.append(this_user)

    def start_raffle(self, channel, amount):
    	if self.is_raffle_active:
    		to_send = "There is already an active raffle!"
    		self.msg(channel, to_send)
    	else:
    	    self.amount_for_raffle = int(amount)
    	    self.raffle_list = []
    	    if amount > 0:
    		    self.is_raffle_active = True
    		    to_send = "A raffle has begun, each raffle ticket is %s points to buy. To buy a ticket type '!raffle <amount of tickets>'." % (str(amount))
    		    self.msg(channel, to_send)

    def handleWinner(self, channel, betname_winner):
        total_pot = 0
        winning_bet_pot = 0
        for item in self.betting_dict[self.betname1]:
            total_pot = total_pot + self.betting_dict[self.betname1][item]
        for item in self.betting_dict[self.betname2]:
            total_pot = total_pot + self.betting_dict[self.betname2][item]
        for item in self.betting_dict[betname_winner]:
            winning_bet_pot = winning_bet_pot + self.betting_dict[betname_winner][item]
        if total_pot == 0:
            pass
        else:
            for item in self.betting_dict[betname_winner]:
                this_bet = self.betting_dict[betname_winner][item]
                points_won = (this_bet * total_pot) / winning_bet_pot
                self.player_points[item] = self.player_points[item] + int(points_won)
        self.is_bet_active = False
        self.is_taking_bets = False
        self.betting_dict = {}
        self.jfile = open(self.jfilename, 'w')
        json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
        self.jfile.close()
        to_send = "And the winner is... %s! Points have now been awarded. Type !mypoints to check your new balance!" % (betname_winner)
        self.msg(channel, to_send)

    def gamble(self, channel, this_user, this_command):
        gamble_amount = int(this_command.split(" ")[1])
        if (this_user in self.player_points.keys()) and (int(self.player_points[this_user]) >= gamble_amount):
            if this_user in self.gamble_players:
                to_send = "Sorry %s, you have gambled too recently, try again in a few minutes" % (this_user)
                self.msg(channel, to_send)
            else:
                random_number = random.randint(0, 100)
                if random_number > 49:
                    self.player_points[this_user] = self.player_points[this_user] + (gamble_amount)
                    self.gamble_players.append(this_user)
                    to_send = "Congratulations %s, you have won %s points with a roll of %s! ElTaco" % (this_user, str(gamble_amount), str(random_number))
                    self.msg(channel, to_send)
                else:
                    self.player_points[this_user] = self.player_points[this_user] - (gamble_amount)
                    self.gamble_players.append(this_user)
                    to_send = "Sorry, %s you have lost %s points with a roll of %s." % (this_user, str(gamble_amount), str(random_number))
                    self.msg(channel, to_send)
        else:
            to_send = "Sorry %s, you do not have enough points for this gamble, type !mypoints to see your points. ElRip" % (this_user)
            self.msg(channel, to_send)
        self.jfile = open(self.jfilename, 'w')
        json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
        self.jfile.close()

    def handlePurchase(self, channel, this_user, this_command):
        to_buy = this_command.split(" ")[1]
        price = int(the_store[to_buy]["price"])
        name = str(the_store[to_buy]["name"])
        if (this_user in self.player_points.keys()) and (self.player_points[this_user] >= price):
            self.player_points[this_user] = self.player_points[this_user] - price
            timedate = datetime.now()
            the_format = "%H:%M:%S %b %d %Y"
            strdate = timedate.strftime(the_format)
            to_save = "Order:\n\tUser: %s\n\tItem: %s\n\tPrice: %s\n\tDate/Time: %s\n\n" % (this_user, the_store[to_buy]["name"], str(price), str(strdate))
            orderfile = open(self.orderfile, 'a')
            orderfile.write(to_save)
            orderfile.close()
            to_send = "Thanks %s, you have purchased a %s for %s points!" % (this_user, the_store[to_buy]["name"], str(price))
            self.msg(channel, to_send)
        else:
            to_send = "Sorry, %s but you don't have enough points to buy '%s', try typing '!mypoints' to view your points." % (this_user, name)
            self.msg(channel, to_send)
        self.jfile = open(self.jfilename, 'w')
        json.dump(self.player_points, self.jfile, indent=4, sort_keys=True)
        self.jfile.close()

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
            print("connection failed:", reason)
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

