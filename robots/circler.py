import os
import sys
import argparse
import time
import signal
import math
import random
from enum import Enum

# include the netbot src directory in sys.path so we can import modules from it.
robotpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(robotpath),"src")
sys.path.insert(0,srcpath)

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_math as nbmath

robotName = "Circler"


def play(botSocket, srvConf):
    SPEED = 100
    CHECK_SPEED_INTERVAL = 2
    BORDER_DIST_MIN = 300
    SLIZE_DEPTH = 3

    gameNumber = 0  # The last game number bot got from the server (0 == no game has been started)
    
    class Border(Enum):
        RIGHT = 0
        TOP = 1
        LEFT = 2
        BOTTOM = 3
    border = Border.RIGHT

    speed_check_counter = 0

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

            # set the initial direction of the bot
            move_direction = math.pi / 2 * border.value
            botSocket.sendRecvMessage({'type': 'setDirectionRequest', 'requestedDirection': move_direction})
            shooting_mode = "scan"


        try:

            getLocationReply = botSocket.sendRecvMessage({'type': 'getLocationRequest'})

            # check the if the distance to the border is smaller than the threshold
            if border == Border.BOTTOM:
                border_dist = getLocationReply['y']
            elif border == Border.LEFT:
                border_dist = getLocationReply['x']
            elif border == Border.TOP:
                border_dist = srvConf['arenaSize'] - getLocationReply['y']
            elif border == Border.RIGHT:
                border_dist = srvConf['arenaSize'] - getLocationReply['x']

            if border_dist < BORDER_DIST_MIN:
                # Change to the next border
                border = Border((border.value + 1) % 4)
                # change the direction of the bot
                move_direction = math.pi / 2 * border.value # right -> 0, bottom -> pi/2, left -> pi, top -> 3*pi/2
                botSocket.sendRecvMessage({'type': 'setDirectionRequest', 'requestedDirection': move_direction})
                # slow down to be able to turn (quickly)
                botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': SPEED/2})

            if speed_check_counter >= CHECK_SPEED_INTERVAL:
                # Check if the bot is moving
                getSpeedReply = botSocket.sendRecvMessage({'type': 'getSpeedRequest'})
                if getSpeedReply['currentSpeed'] == 0:
                    # change the direction to avoid getting stuck
                    border = Border((border.value + 1) % 4)
                    move_direction = math.pi / 2 * border.value
                    botSocket.sendRecvMessage({'type': 'setDirectionRequest', 'requestedDirection': move_direction})
                    botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': SPEED/2})
                else:
                    # if the bot has turned and moves into the right direction, set the speed to the normal speed
                    getDirectionReply = botSocket.sendRecvMessage({'type': 'getDirectionRequest'})
                    if getDirectionReply['currentDirection'] == move_direction:
                        botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': SPEED})

                speed_check_counter = 0
            else:
                speed_check_counter += 1


            if shooting_mode == "wait":
                # find out if we already have a shell in the air. We need to wait for it to explode before
                # we fire another shell. If we don't then the first shell will never explode!
                getCanonReply = botSocket.sendRecvMessage({'type': 'getCanonRequest'})
                if not getCanonReply['shellInProgress']:
                    # we are ready to shoot again!
                    shooting_mode = "scan"
            elif shooting_mode == "scan":
                interval_start = 0
                for i in range(SLIZE_DEPTH):
                    interval_width = math.pi / 2 ** i
                    # scan the interval
                    scanReply = botSocket.sendRecvMessage(
                        {'type': 'scanRequest', 'startRadians': interval_start, 'endRadians': interval_start + interval_width})

                    print(f"Scan {i}: Start: {interval_start}, Width: {interval_width}, Distance: {scanReply['distance']}")
                    # check if there are any enemies in the scanned area
                    if scanReply['distance'] == 0:
                        # it is empty, so it needs to be in the other half
                        if i != SLIZE_DEPTH - 1:
                            interval_start += interval_width
                            continue


                    if i == SLIZE_DEPTH - 1:
                        # we are in the last slice, that should contain the enemy, so we fire at it
                        if scanReply['distance'] == 0:
                            # here we know that there is an enemy in the half starting at interval_start, but we don't have the distance, so we scan again
                            scanReply = botSocket.sendRecvMessage(
                                {'type': 'scanRequest', 'startRadians': interval_start + interval_width, 'endRadians': interval_start + 2*interval_width})
                            # if it is empty now, the movement of the bots caused them to move out of the area, so we continue without firing
                            if scanReply['distance'] == 0:
                                print(f"No enemy found in last scan at {interval_start} with width {interval_width / 2}")
                                continue
                            interval_start += interval_width
                        fireDirection = interval_start + interval_width / 2
                        botSocket.sendRecvMessage(
                            {'type': 'fireCanonRequest', 'direction': fireDirection, 'distance': scanReply['distance']})
                        shooting_mode = "wait"
                        print(f"Fired at enemy in direction {fireDirection} with distance {scanReply['distance']}")


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
