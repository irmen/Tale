import datetime

class GameConfig(object):
    name = "Snakepit"
    version = "0.5"                 # arbitrary but is used to check savegames for compatibility
    requires_tale = "0.4"           # tale library required to run the game
    max_score = 00                 # arbitrary, but when max score is reached, the game is supposed to end. Use 0 or None to disable scoring.
    server_tick_method = "timer"    # 'command' (waits for player entry) or 'timer' (async timer driven)
    server_tick_time = 1.0          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
    gametime_to_realtime = 5.0      # meaning: game time is X times the speed of real time (only used with "timer" tick method)
    epoch = datetime.datetime(2012, 4, 19, 14, 0, 0)    # start date/time of the game clock
    display_gametime = True         # enable/disable display of the game time at certain moments
    startlocation_player = "town.square"
    startlocation_wizard = "wizardtower.hall"


def init(driver):
    pass
