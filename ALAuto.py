import sys
import traceback
import argparse
from modules.combat import CombatModule
from modules.commission import CommissionModule
from modules.enhancement import EnhancementModule
from modules.mission import MissionModule
from modules.retirement import RetirementModule
from modules.headquarters import HeadquartersModule
from modules.event import EventModule
from datetime import datetime, timedelta
from util.adb import Adb
from util.updater import UpdateUtil
from util.config import Config
from util.logger import Logger
from util.stats import Stats
from util.utils import Utils, Region

class ALAuto(object):
    modules = {
        'updates': None,
        'combat': None,
        'commissions': None,
        'enhancement': None,
        'missions': None,
        'retirement': None,
        'headquarters': None,
        'event': None
    }

    def __init__(self, config):
        """Initializes the primary azurlane-auto instance with the passed in
        Config instance; creates the Stats instance and resets scheduled sleep
        timers.

        Args:
            config (Config): azurlane-auto Config instance
        """
        self.config = config
        self.oil_limit = 0
        self.stats = Stats(config)
        if self.config.updates['enabled']:
            self.modules['updates'] = UpdateUtil(self.config)
        if self.config.combat['enabled']:
            self.modules['combat'] = CombatModule(self.config, self.stats)
            self.oil_limit = self.config.combat['oil_limit']
        if self.config.commissions['enabled']:
            self.modules['commissions'] = CommissionModule(self.config, self.stats)
        if self.config.enhancement['enabled']:
            self.modules['enhancement'] = EnhancementModule(self.config, self.stats)
        if self.config.missions['enabled']:
            self.modules['missions'] = MissionModule(self.config, self.stats)
        if self.config.retirement['enabled']:
            self.modules['retirement'] = RetirementModule(self.config, self.stats)
        if self.config.dorm['enabled'] or self.config.academy['enabled']:
            self.modules['headquarters'] = HeadquartersModule(self.config, self.stats)
        if self.config.events['enabled']:
            self.modules['event'] = EventModule(self.config, self.stats)
        self.print_stats_check = True
        self.next_combat = datetime.now()

    def run_update_check(self):
        if self.modules['updates']:
            if self.modules['updates'].checkUpdate():
                Logger.log_warning("A new release is available, please check the github.")

    def should_sortie(self):
        """Method to check wether bot should combat or not.
        """
        return self.modules['combat'] \
            and script.next_combat != 0 \
            and script.next_combat < datetime.now() \
            and Utils.check_oil(self.oil_limit)

    def run_sortie_cycle(self):
        """Method to run all cycles related to combat.
        """
        self.run_event_cycle()
        self.run_combat_cycle()
        self.run_enhancement_cycle()
        self.run_retirement_cycle()

    def run_combat_cycle(self):
        """Method to run the combat cycle.
        """
        if self.modules['combat']:
            result = self.modules['combat'].combat_logic_wrapper()

            if result == 1:
                # if boss is defeated
                Logger.log_msg("Boss successfully defeated, going back to menu.")
                self.print_stats_check = True
            if result == 2:
                # if morale is too low
                Logger.log_warning("Ships morale is too low, entering standby mode for an hour.")
                self.next_combat = datetime.now() + timedelta(hours=1)
                self.print_stats_check = False
            if result == 3:
                # if dock is full
                Logger.log_warning("Dock is full, need to retire.")

                if self.modules['retirement']:
                    self.modules['retirement'].retirement_logic_wrapper(True)
                else:
                    Logger.log_error("Retirement isn't enabled, exiting.")
                    sys.exit()
            if result == 4:
                Logger.log_warning("Failed to defeat enemy.")
                self.print_stats_check = False
        else:
            self.next_combat = 0

    def run_commission_cycle(self):
        """Method to run the expedition cycle.
        """
        if self.modules['commissions']:
            self.modules['commissions'].commission_logic_wrapper()

    def run_enhancement_cycle(self):
        """Method to run the enhancement cycle.
        """
        if self.modules['enhancement']:
            self.modules['enhancement'].enhancement_logic_wrapper()

    def run_mission_cycle(self):
        """Method to run the mission cycle
        """
        if self.modules['missions']:
            self.modules['missions'].mission_logic_wrapper()

    def run_retirement_cycle(self):
        """Method to run the retirement cycle
        """
        if self.modules['retirement']:
            self.modules['retirement'].retirement_logic_wrapper()

    def run_hq_cycle(self):
        """Method to run the headquarters cycle.
        """
        if self.modules['headquarters']:
            self.modules['headquarters'].hq_logic_wrapper()

    def run_event_cycle(self):
        """Method to run the event cycle
        """
        if self.modules['event']:
            self.modules['event'].event_logic_wrapper()

    def print_cycle_stats(self):
        """Method to print the cycle stats"
        """
        if self.print_stats_check:
            self.stats.print_stats(Utils.check_oil(self.oil_limit))
        self.print_stats_check = False

# check run-time args
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config',
                    metavar=('CONFIG_FILE'),
                    help='Use the specified configuration file instead ' +
                         'of the default config.ini')
parser.add_argument('-d', '--debug',
                    help='Enables debugging logs.', action='store_true')
parser.add_argument('-l', '--legacy',
                    help='Enables sed usage.', action='store_true')
args = parser.parse_args()

# check args, and if none provided, load default config
if args:
    if args.config:
        config = Config(args.config)
    else:
        config = Config('config.ini')
    if args.debug:
        Logger.log_info("Enabled debugging.")
        Logger.enable_debugging(Logger)
    if args.legacy:
        Logger.log_info("Enabled sed usage.")
        Adb.enable_legacy(Adb)

script = ALAuto(config)
script.run_update_check()

Adb.service = config.network['service']
Adb.device = '-d' if (Adb.service == 'PHONE') else '-e'
adb = Adb()

if adb.init():
    Logger.log_msg('Successfully connected to the service.')
    res = ['1920x1080', '1080x1920']

    if Adb.exec_out('wm size').decode('utf-8').strip()[15:] not in res:
        Logger.log_error("Resolution is not 1920x1080, please change it.")
        sys.exit()

    Utils.assets = config.assets['server']
else:
    Logger.log_error('Unable to connect to the service.')
    sys.exit()

try:
    while True:
        Utils.wait_update_screen(1)

        # temporal solution to event alerts
        # if not Utils.find("menu/button_battle"):
        #     Utils.touch_randomly(Region(54, 57, 67, 67))
        #     Utils.script_sleep(1)
        #     continue

        Utils.avoid_stuck_routine()

        if Utils.find("commission/alert_completed"):
            script.run_commission_cycle()
            script.print_cycle_stats()
        if Utils.find("mission/alert_completed"):
            script.run_mission_cycle()
        if Utils.find("headquarters/hq_alert"):
            script.run_hq_cycle()
        if script.should_sortie():
            script.run_sortie_cycle()
            script.print_cycle_stats()
        else:
            Logger.log_msg("Nothing to do, will check again in a few minutes.")
            Utils.script_sleep(60)
            continue
except KeyboardInterrupt:
    # handling ^C from user
    Logger.log_msg("Received keyboard interrupt from user. Closing...")
    # writing traceback to file
    f = open("traceback.log", "w")
    traceback.print_exc(None, f, True)
    f.close()
    script.stats.print_stats(0)
    sys.exit(0)
except:
    # registering whatever exception occurs during execution
    Logger.log_error("An error occurred. For more info check the traceback.log file.")
    # writing traceback to file
    f = open("traceback.log", "w")
    traceback.print_exc(None, f, True)
    f.close()
    sys.exit(1)