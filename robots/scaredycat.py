import os
import sys
import argparse
import time
import signal
import math
import random

# include the netbot src directory in sys.path so we can import modules from it.
robotpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(robotpath),"src")
sys.path.insert(0,srcpath)

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_math as nbmath

robotName = "ScaredyCat v1" #Written by Michael Chen @MCSnapTurtle


def play(botSocket, srvConf):
    gameNumber = 0  # The last game number bot got from the server (0 == no game has been started)

    while True:
        try:
            # Get information to determine if bot is alive (health > 0) and if a new game has started.
            getInfoReply = botSocket.sendRecvMessage({'type': 'getInfoRequest'})
        except nbipc.NetBotSocketException as e:
            # We are always allowed to make getInfoRequests, even if our health == 0. Something serious has gone wrong.
            log(str(e), "FAILURE")
            log("Is netbot server still running?")
            quit()

        if getInfoReply['health'] == 0:
            # we are dead, there is nothing we can do until we are alive again.
            continue

        if getInfoReply['gameNumber'] != gameNumber:
            # A new game has started. Record new gameNumber and reset any variables back to their initial state
            gameNumber = getInfoReply['gameNumber']
            log("Game " + str(gameNumber) + " has started. Points so far = " + str(getInfoReply['points']))

            # The distance to the closest bot in each quadrant is stored in this list.
            quadrant = [0, 0, 0, 0]


        try:

            # if ScaredyCat is at the arena boundary, it should stop
            getLocationReply = botSocket.sendRecvMessage({'type': 'getLocationRequest'})
            if round(getLocationReply['x']) == srvConf['botRadius'] + 1 :
                botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 0})
            elif round(getLocationReply['x']) == srvConf['arenaSize'] - srvConf['botRadius'] - 1:
                botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 0})
            elif round(getLocationReply['y']) == srvConf['botRadius'] + 1:
                botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 0})
            elif round(getLocationReply['y']) == srvConf['arenaSize'] - srvConf['botRadius'] - 1:
                botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 0})
            else:

                # variables that are iterated in the while loop
                x = 0
                i = 0

                # ScaredyCat scans all four quadrants and looks for the closest target
                while x < 2.0:

                    # ScaredyCat scans the quadrant starting from x pi to 1/2 more than x. This is a quarter of a circle.
                    # Then , it adds the server's response to the list
                    scanReply = botSocket.sendRecvMessage({'type': 'scanRequest', 'startRadians': math.pi*x, 'endRadians': math.pi*(x + 1.0/2.0)})
                    quadrant[i] = scanReply['distance']
                    x += 1.0/2.0
                    i += 1

                # finds how far the closest enemy is from us (can't be zero)
                minDistance = min(i for i in quadrant if i > 0)

                # finds which quadrant that enemy is in
                moveDirection = quadrant.index(minDistance)

                # move in the opposite direction of the quandrant where the closest enemy is at, at a 45 degree angle.
                # ie. if closest enemy is in quadrant 3, it will move in the direction pi * 1.0/4.0 in the first quadrant
                if moveDirection == 0:
                    moveDirection = math.pi * (5.0/4.0)
                elif moveDirection == 1:
                    moveDirection = math.pi * (7.0 / 4.0)
                elif moveDirection == 2:
                    moveDirection = math.pi * (1.0 / 4.0)
                elif moveDirection == 3:
                    moveDirection = math.pi * (3.0 / 4.0)

                # Turn in a new direction
                

                # Request we start accelerating to max speed
                botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 30})

        except nbipc.NetBotSocketException as e:
            # Consider this a warning here. It may simply be that a request returned
            # an Error reply because our health == 0 since we last checked. We can
            # continue until the next game starts.
            log(str(e), "WARNING")
            continue

##################################################################
# Standard stuff below.
##################################################################


def quit(signal=None, frame=None):
    global botSocket
    log(botSocket.getStats())
    log("Quiting", "INFO")
    exit()


def main():
    global botSocket  # This is global so quit() can print stats in botSocket
    global robotName

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ip', metavar='My IP', dest='myIP', type=nbipc.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='My Port', dest='myPort', type=int, nargs='?',
                        default=20010, help='My port number')
    parser.add_argument('-sip', metavar='Server IP', dest='serverIP', type=nbipc.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='Server IP Address')
    parser.add_argument('-sp', metavar='Server Port', dest='serverPort', type=int, nargs='?',
                        default=20000, help='Server port number')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    args = parser.parse_args()
    setLogLevel(args.debug, args.verbose)

    try:
        botSocket = nbipc.NetBotSocket(args.myIP, args.myPort, args.serverIP, args.serverPort)
        joinReply = botSocket.sendRecvMessage({'type': 'joinRequest', 'name': robotName}, retries=300, delay=1, delayMultiplier=1)
    except nbipc.NetBotSocketException as e:
        log("Is netbot server running at" + args.serverIP + ":" + str(args.serverPort) + "?")
        log(str(e), "FAILURE")
        quit()

    log("Join server was successful. We are ready to play!")

    # the server configuration tells us all about how big the arena is and other useful stuff.
    srvConf = joinReply['conf']
    log(str(srvConf), "VERBOSE")

    # Now we can play, but we may have to wait for a game to start.
    play(botSocket, srvConf)


if __name__ == "__main__":
    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
