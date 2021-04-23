#!/usr/bin/env python3

import os
import time
import datetime

from bluepy import btle
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, Characteristic, ScanEntry, Service, UUID
import curses
import curses.textpad
from carcontrol import CarControl

# Scan timeout in seconds
SCAN_TIMEOUT = 10

## screen parts
LINE_HEADING = 0
LINE_OPTIONS = 1
LINE_STATUS = 5
LINE_ERROR = 6
COL_START = 0

HEIGHT_TOP = 8
HEIGHT_BOT = 3

LOOP_DURATION = 0.05
DISPLAY_COUNT = 100

LINE_RECT = 30
RECT_HEIGHT = 12
RECT_WIDTH = 40

MSG_WELCOME = "Welcome to Carmageddon - in real life!\n"
MSG_OPTIONS               = "  [S] - start scanning...\t\t\t\t[Q] - Exit\n"
MSG_OPTIONS = MSG_OPTIONS + "  [1...9] - Direct connect to device by number\t\t[D] - Disconnect \n"
MSG_DRIVE_HELP = "Use [Arrows] to drive, [SPACE] to Fire"


class MainScreen:
    
    status = 0
    lastmsg = None
    lasterror = None
    displaycounter = 0
    car = CarControl()
    
    def __init__(self):
        curses.wrapper(self.mainloop)
    
    def createmidwin(self):
        win = curses.newwin(curses.LINES - (HEIGHT_TOP + HEIGHT_BOT), curses.COLS, HEIGHT_TOP, COL_START)
        win.scrollok(True)
        win.idlok(True)
        win.addstr(LINE_HEADING, COL_START, "Information:", curses.A_BOLD)
        win.move(0, 0)
        win.refresh()
        return win

    
    def createbotwin(self):
        win = curses.newwin(HEIGHT_BOT, curses.COLS, curses.LINES - HEIGHT_BOT, COL_START)
        win.addstr(LINE_HEADING, COL_START, "Bot window", curses.A_BOLD)
        win.move(0, 0)
        win.refresh()
        return win
        
    def drawheadings(self, window):
        window.addstr(LINE_HEADING, COL_START, MSG_WELCOME, curses.A_BOLD)
        window.addstr(LINE_OPTIONS, COL_START, MSG_OPTIONS)
        window.hline('_', curses.COLS)
        window.refresh()
        
    def resizescreen(self, midwin, botwin):
        midwin.resize(curses.LINES - (HEIGHT_TOP + HEIGHT_BOT), curses.COLS)
        botwin.mvwin(curses.LINES - HEIGHT_TOP - 1, COL_START)

    def updatestatus(self, window, status=0, msg="", error=""):
        self.status = status
        self.lastmsg = msg
        self.lasterror = error

        if window is None:
            return
        
        statusmsg = "Status: {} - {}".format(self.status, self.lastmsg)
        errmsg = "Error: {}".format(self.lasterror) if len(self.lasterror) > 0 else ""
        
        window.move(LINE_STATUS, COL_START)
        window.addstr(LINE_STATUS, COL_START, statusmsg)
        window.clrtoeol()

        window.move(LINE_ERROR, COL_START)
        window.addstr(LINE_ERROR, COL_START, errmsg)
        window.clrtoeol()
        
        window.refresh()
        
    
    def countdownstatus(self):
        self.displaycounter = DISPLAY_COUNT
        
    def checkstatus(self):
        if self.displaycounter > 1 and self.status > 0:
            self.displaycounter = self.displaycounter - 1
            return False
        elif self.displaycounter == 1 and self.status > 0:
            self.status = 0
            self.displaycounter = 0
            return True
        else:
            return False

    def detailline(self, window, msg=""):
        window.clear()
        window.move(0, COL_START)
        window.addstr("{}".format(msg))
        window.refresh()
        window.move(0, COL_START)

    def debugline(self, window, msg=""):
        window.move(0, COL_START)
        window.addstr("dbg: {}".format(msg))
        window.clrtoeol()
        window.refresh()
        
    
    def mainloop(self, stdscr):
        
        self.drawheadings(stdscr)
        self.updatestatus(stdscr)
        
        midwin = self.createmidwin()
        botwin = self.createbotwin()
        self.debugline(botwin)
        
        stdscr.nodelay(True)
        
        while True:
            time.sleep(LOOP_DURATION)

            if self.checkstatus():
                self.updatestatus(stdscr)
            
            inchar = stdscr.getch()
            curses.flushinp()
            # SCAN
            if inchar == ord('s') or inchar == ord('S'):
                self.updatestatus(stdscr, 1, "Scanning...")
                self.detailline(midwin)
                if self.car.scan(SCAN_TIMEOUT):
                    self.updatestatus(stdscr, 1, "Scan - Done, found {} devices".format(len(self.car.devices)))
                else:
                    #self.updatestatus(stdscr, 1, "Scan - Error", "Could not initiate scanning")
                    self.updatestatus(stdscr, 1, "Scan - Error with scan, found {} devices".format(len(self.car.devices)))
                    #self.countdownstatus()
                self.detailline(midwin, self.car.devicetext)
                self.debugline(botwin, "{}".format(self.car))
            # Connect
            elif inchar >= ord('1') and inchar <= ord('9'):
                devnum = inchar - ord('1') + 1
                self.debugline(botwin, "Device #{}".format(devnum))
                self.updatestatus(stdscr, 2, "Connecting to car #{}...".format(devnum))
                if self.car.connect((devnum-1)):
                    self.updatestatus(stdscr, 2, "Connected to car #{} [{}]...".format(devnum, self.car.carName))
                    self.debugline(botwin, "Sending handshake...")
                    self.car.sendhandshake()
                    self.debugline(botwin, "Sending handshake, Done")
                    self.detailline(midwin, MSG_DRIVE_HELP)
                else:
                    self.updatestatus(stdscr, 2, "No connection to car #{}...".format(devnum))
                self.debugline(botwin, "{}".format(self.car))
            # Disconnect
            elif inchar == ord('d') or inchar == ord('D'):
                self.updatestatus(stdscr, 3, "Disconnecting...")
                if self.car.disconnectcar():
                    self.updatestatus(stdscr, 2, "Disconnect, Done")
                else:
                    self.updatestatus(stdscr, 2, "Unable to disconnect car")
                self.detailline(midwin)
                self.debugline(botwin, "{}".format(self.car))
            # Quit
            elif inchar == ord('q') or inchar == ord('Q'):
                if self.car.isConnected: self.car.disconnectcar();
                break
            
            # Movement Actions
            elif inchar == ord(' '):
                if self.car.isConnected: self.car.carfiregun()
            elif inchar == curses.KEY_UP:
                if self.car.isConnected: self.car.carforward()
            elif inchar == curses.KEY_DOWN:
                if self.car.isConnected: self.car.carreverse()
            elif inchar == curses.KEY_LEFT:
                if self.car.isConnected: self.car.carleft()
            elif inchar == curses.KEY_RIGHT:
                if self.car.isConnected: self.car.carright()
            elif inchar == curses.KEY_RESIZE:
                curses.update_lines_cols()
                self.resizescreen(midwin, botwin)
                self.debugline(botwin, "resizing")
                self.drawheadings(stdscr)
                self.updatestatus(stdscr)
            elif inchar == curses.ERR or inchar == -1:
                continue
            else:
                continue
                


if __name__ == '__main__':
    
    try:
        screen = MainScreen()
    except KeyboardInterrupt:
        os.sys.exit(0)
#    finally:
