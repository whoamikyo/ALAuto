from util.logger import Logger
from util.utils import Region, Utils
from util.config import Config

class DailyModule(object):

    def __init__(self, config, stats):
        """Initializes the Expedition module.
        Args:
            config (Config): kcauto Config instance
        """
        self.enabled = True
        self.config = config
        self.stats = stats
        self.region = {
            'menu_button_battle': Region(1518, 440, 207, 203),
            'announcement': Region(1770, 77, 49, 47),
            'start_daily': Region(1125, 978, 212, 71),
            'center_daily': Region(797, 218, 322, 419),
            'select_daily': Region(578, 211, 100, 42),
            'menu_combat_start': Region(1578, 921, 270, 70),
            'tap_to_continue': Region(661, 840, 598, 203),
            'combat_end_confirm': Region(1520, 963, 216, 58),
            'menu_nav_back': Region(54, 57, 67, 67),
            'swipe': Region(1838, 516, 45, 52),
            'home_button': Region(1842, 32, 39, 35)
        }

    def daily_logic_wrapper(self):
        """Method that fires off the necessary child methods that encapsulates
        the entire action of sortieing combat fleets and resolving combat.
        """
        Utils.update_screen()

        while True:

            if Utils.find("menu/button_battle"):
                Logger.log_debug("Found menu battle button.")
                Utils.touch_randomly(self.region["menu_button_battle"])
                Utils.wait_update_screen(1)
                continue
            if Utils.find("combat/daily_menu"):
                Logger.log_debug("Found Daily Raid button.")
                Utils.touch_randomly(self.region["start_daily"])
                Utils.wait_update_screen(1)
                continue
            if Utils.find("combat/daily_locked3"):
                self.swipe()
            if Utils.find("combat/tactical_training") and not Utils.find("combat/tactical_training_out") and not Utils.find("combat/daily_locked"):
                self.select_daily()
            else:
                self.swipe()
            if Utils.find("combat/advance_mission") and not Utils.find("combat/advance_mission_out") and not Utils.find("combat/daily_locked"):
                self.select_daily()
            else:
                self.swipe()
            if Utils.find("combat/escort_mission") and not Utils.find("combat/escort_mission_out") and not Utils.find("combat/daily_locked"):
                self.select_daily()
            else:
                self.swipe()
            if Utils.find("combat/supply_line"):
                Logger.log_info("Supply line is not supported yet.")
                Utils.touch_randomly(self.region["swipe"])
                Utils.wait_update_screen(1)
            if Utils.find("combat/fierce_assault"):
                Logger.log_info("Fierce assault is not supported yet.")
                Utils.touch_randomly(self.region["swipe"])
                Utils.wait_update_screen(1)
            if Utils.find("menu/home_button"):
                Logger.log_info("Back to main screen.")
                Utils.touch_randomly(self.region["home_button"])
                break

    def swipe(self):

        Utils.touch_randomly(self.region["swipe"])
        Logger.log_info("You're out of daily stage challenges.")
        Utils.wait_update_screen(1)

    def select_daily(self):

        Utils.wait_update_screen(1)

        # while True:

        if not Utils.find("combat/daily_attempts"):
            Utils.touch_randomly(self.region["center_daily"])
            Logger.log_info("Found daily challenge.")
            Utils.script_sleep(1)
            Utils.update_screen()
                # continue
        if Utils.find("combat/daily_attempts"):
            Utils.touch_randomly(self.region["select_daily"])
            Logger.log_info("Select daily challenge.")
            Utils.script_sleep(1)
            Utils.update_screen()
                # continue
        if Utils.find("combat/daily_out"):
            Logger.log_info("You're out of daily stage challenges.")
            Utils.touch_randomly(self.region["menu_nav_back"])
                # return True
        Utils.wait_update_screen(1)

        self.start_daily()

    def start_daily(self):

        while True:

            if Utils.find("combat/battle_button"):
                Utils.touch_randomly(self.region["menu_combat_start"])
                Logger.log_debug("Found battle button, starting clear function.")
                self.daily_handler()
            if Utils.find("combat/daily_out"):
                Logger.log_info("You're out of daily stage challenges.")
                Utils.touch_randomly(self.region["menu_nav_back"])
            Utils.update_screen()

    def daily_handler(self):

        Logger.log_msg("Starting combat.")

        while not (Utils.find("combat/menu_loading", 0.8)):
            Utils.update_screen()

            if Utils.find("combat/combat_pause", 0.7):
                Logger.log_warning("Loading screen was not found but combat pause is present, assuming combat is initiated normally.")
                break
            else:
                Utils.touch_randomly(self.region["menu_combat_start"])
                Utils.script_sleep(1)

        Utils.script_sleep(4)

        while True:
            Utils.update_screen()

            if Utils.find("combat/combat_pause", 0.7):
                Logger.log_debug("In battle.")
                Utils.script_sleep(5)
                continue
            if Utils.find("combat/menu_touch2continue"):
                Utils.touch_randomly(self.region['tap_to_continue'])
                continue
            if Utils.find("menu/item_found"):
                Utils.touch_randomly(self.region['tap_to_continue'])
                Utils.script_sleep(1)
                continue
            if Utils.find("combat/button_confirm"):
                Logger.log_msg("Combat ended.")
                Utils.touch_randomly(self.region["combat_end_confirm"])
                Utils.script_sleep(1)

            Utils.update_screen()
            self.select_daily()

