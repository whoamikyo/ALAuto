import configparser
import sys
import re
from copy import deepcopy
from util.logger import Logger
import util.config_consts


class Config(object):
    """Config module that reads and validates the config to be passed to
    azurlane-auto
    """

    def __init__(self, config_file):
        """Initializes the config file by changing the working directory to the
        root azurlane-auto folder and reading the passed in config file.

        Args:
            config_file (string): Name of config file.
        """
        Logger.log_msg("Initializing config module")
        self.config_file = config_file
        self.ok = False
        self.initialized = False
        self.updates = {'enabled': False}
        self.combat = {'enabled': False}
        self.commissions = {'enabled': False}
        self.enhancement = {'enabled': False}
        self.missions = {'enabled': False}
        self.retirement = {'enabled': False}
        self.dorm = {'enabled': False}
        self.academy = {'enabled': False}
        self.research = {'enabled': False}
        self.events = {'enabled': False}
        self.drop_rates = {'enabled': False}
        self.network = {}
        self.assets = {}
        self.screenshot = {}
        self.read()

    def try_cast_to_int(self, val):
        """Helper function that attempts to coerce the val to an int,
        returning the val as-is the cast fails
        Args:
            val (string): string to attempt to cast to int
        Returns:
            int, str: int if the cast was successful; the original str
                representation otherwise
        """
        try:
            return int(val)
        except ValueError:
            return val

    def try_cast_to_float(self, val):
        """Helper function that attempts to coerce the val to a float,
        returning the val as-is the cast fails
        Args:
            val (string): string to attempt to cast to float
        Returns:
            float, str: float if the cast was successful; the original str
                representation otherwise
        """
        try:
            return float(val)
        except ValueError:
            return val

    def read(self):

        backup_config = deepcopy(self.__dict__)
        config = configparser.ConfigParser()
        config.read(self.config_file)
        self.network['service'] = config.get('Network', 'Service')
        self._read_screenshot(config)

        self.assets['server'] = config.get('Assets', 'Server')

        if config.getboolean('Updates', 'Enabled'):
            self._read_updates(config)

        if config.getboolean('Combat', 'Enabled'):
            self._read_combat(config)

        if config.getboolean('Headquarters', 'Dorm') or config.getboolean('Headquarters', 'Academy'):
            self._read_headquarters(config)

        self.commissions['enabled'] = config.getboolean('Modules', 'Commissions')
        self.missions['enabled'] = config.getboolean('Modules', 'Missions')

        if config.getboolean('Enhancement', 'Enabled'):
            self._read_enhancement(config)

        if 'Retirement' in config:
            # New retirement settings
            self.retirement['enabled'] = config.getboolean('Retirement', 'enabled', fallback=False)
            self.retirement['rares'] = config.getboolean('Retirement', 'Rares', fallback=True)
            self.retirement['commons'] = config.getboolean('Retirement', 'Commons', fallback=True)
        elif 'Retirement' in config['Modules']:
            # Legacy retirement setting. Maintain classic rare retirement behavior
            self.retirement['enabled'] = config.getboolean('Modules', 'Retirement')
            self.retirement['rares'] = True
            self.retirement['commons'] = True

        if config.getboolean('Research', 'Enabled'):
            self._read_research(config)

        if config.getboolean('Events', 'Enabled'):
            self._read_event(config)

        if config.getboolean('DropRates', 'Enabled'):
            self._read_droprates(config)

        self.validate()
        if (self.ok and not self.initialized):
            Logger.log_msg("Starting ALAuto!")
            if self.combat['enabled'] and self.combat['ignore_morale']:
                Logger.log_warning("Ignore morale is enabled")
            self.initialized = True
            self.changed = True
        elif (not self.ok and not self.initialized):
            Logger.log_error("Invalid config. Please check your config file.")
            sys.exit(1)
        elif (not self.ok and self.initialized):
            Logger.log_warning("Config change detected, but with problems. Rolling back config.")
            self._rollback_config(backup_config)
        elif (self.ok and self.initialized):
            if backup_config != self.__dict__:
                Logger.log_warning("Config change detected. Hot-reloading.")
                self.changed = True

    def _read_screenshot(self, config):
        """Method to parse the Updates settings of the passed in config.
            Args:
                config (ConfigParser): ConfigParser instance
        """

        consts = util.config_consts.UtilConsts.ScreenCapMode
        self.screenshot['mode'] = self._validate_list(config.get('Screenshot', 'Mode'), min_len=1, max_len=1,
                                                      valid_vals=['SCREENCAP_PNG', 'SCREENCAP_RAW', 'ASCREENCAP'],
                                                      map_vals=[consts.SCREENCAP_PNG, consts.SCREENCAP_RAW,
                                                                consts.ASCREENCAP],
                                                      cast=lambda x: x.upper())[0]

    def _read_updates(self, config):
        """Method to parse the Updates settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.updates['enabled'] = True
        self.updates['channel'] = config.get('Updates', 'Channel')

    def _read_combat(self, config):
        """Method to parse the Combat settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.combat['enabled'] = True
        self.combat['map'] = config.get('Combat', 'Map')
        self.combat['kills_before_boss'] = self.try_cast_to_int(config.get('Combat', 'KillsBeforeBoss'))
        self.combat['boss_fleet'] = config.getboolean('Combat', 'BossFleet')
        self.combat['flip_fleets'] = config.getboolean('Combat', 'FlipFleets')
        self.combat['oil_limit'] = self.try_cast_to_int(config.get('Combat', 'OilLimit'))
        self.combat['retire_cycle'] = self.try_cast_to_int(config.get('Combat', 'RetireCycle'))
        self.combat['retreat_after'] = self.try_cast_to_int(config.get('Combat', 'RetreatAfter'))
        self.combat['ignore_mystery_nodes'] = config.getboolean('Combat', 'IgnoreMysteryNodes')
        self.combat['focus_on_mystery_nodes'] = config.getboolean('Combat', 'FocusOnMysteryNodes')
        self.combat['clearing_mode'] = config.getboolean('Combat', 'ClearingMode')
        self.combat['hide_subs_hunting_range'] = config.getboolean('Combat', 'HideSubsHuntingRange')
        self.combat['small_boss_icon'] = config.getboolean('Combat', 'SmallBossIcon')
        self.combat['siren_elites'] = config.getboolean('Combat', 'SirenElites')
        self.combat['ignore_morale'] = config.getboolean('Combat', 'IgnoreMorale')
        self.combat['low_mood_sleep_time'] = self.try_cast_to_float(config.get('Combat', 'LowMoodSleepTime'))
        self.combat['search_mode'] = self.try_cast_to_int(config.get('Combat', 'SearchMode'))

    def _read_headquarters(self, config):
        """Method to parse the Headquarters settings passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.dorm['enabled'] = config.getboolean('Headquarters', 'Dorm')
        if self.dorm['enabled']:
            self.dorm['AvailableSupplies'] = self._validate_list(config.get('Headquarters', 'AvailableSupplies'),
                                                                 valid_vals=[1000, 2000, 3000, 5000, 10000, 20000],
                                                                 min_len=1, max_len=6, cast=int, unique=True)
        self.academy['enabled'] = config.getboolean('Headquarters', 'Academy')
        if self.academy['enabled']:
            self.academy['skill_book_tier'] = self.try_cast_to_int(config.get('Headquarters', 'SkillBookTier'))

    def _read_enhancement(self, config):
        """Method to parse the Enhancement settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.enhancement['enabled'] = True
        self.enhancement['single_enhancement'] = config.getboolean('Enhancement', 'SingleEnhancement')

    def _read_research(self, config):
        """Method to parse the Research settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.research['enabled'] = True
        self.research['AllowFreeProjects'] = config.getboolean('Research', 'AllowFreeProjects')
        self.research['AllowConsumingCoins'] = config.getboolean('Research', 'AllowConsumingCoins')
        self.research['AllowConsumingCubes'] = config.getboolean('Research', 'AllowConsumingCubes')
        self.research['WithoutRequirements'] = config.getboolean('Research', 'WithoutRequirements')
        self.research['AwardMustContainPRBlueprint'] = config.getboolean('Research', 'AwardMustContainPRBlueprint')
        self.research['30Minutes'] = config.getboolean('Research', '30Minutes')
        self.research['1Hour'] = config.getboolean('Research', '1Hour')
        self.research['1Hour30Minutes'] = config.getboolean('Research', '1Hour30Minutes')
        self.research['2Hours'] = config.getboolean('Research', '2Hours')
        self.research['2Hours30Minutes'] = config.getboolean('Research', '2Hours30Minutes')
        self.research['4Hours'] = config.getboolean('Research', '4Hours')
        self.research['5Hours'] = config.getboolean('Research', '5Hours')
        self.research['6Hours'] = config.getboolean('Research', '6Hours')
        self.research['8Hours'] = config.getboolean('Research', '8Hours')
        self.research['12Hours'] = config.getboolean('Research', '12Hours')

    def _read_event(self, config):
        """Method to parse the Event settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.events['enabled'] = True
        self.events['name'] = config.get('Events', 'Event')
        self.events['levels'] = config.get('Events', 'Levels').split(',')
        self.events['ignore_rateup'] = config.getboolean('Events', 'IgnoreRateUp')

    def _read_droprates(self, config):
        """Method to parse the Drop Rate Research settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.drop_rates['enabled'] = True
        self.drop_rates['ComissionDrops'] = config.getboolean('DropRates', 'ComissionDrops')
        self.drop_rates['MapDrops'] = config.getboolean('DropRates', 'MapDrops')
        self.drop_rates['ResearchDrops'] = config.getboolean('DropRates', 'ResearchDrops')

    def validate(self):
        """Method to validate the passed in config file
        """
        if not self.initialized:
          Logger.log_msg("Validating config")
        self.ok = True

        valid_servers = ['EN', 'JP']
        if self.assets['server'] not in valid_servers:
            if len(valid_servers) < 2:
                Logger.log_error("Invalid server assets configured. Only {} is supported.".format(''.join(valid_servers)))
            else:
                Logger.log_error("Invalid server assets configured. Only {} and {} are supported.".format(', '.join(valid_servers[:-1]), valid_servers[-1]))
            self.ok = False

        if not self.combat['enabled'] and not self.commissions['enabled'] and not self.enhancement['enabled'] \
           and not self.missions['enabled'] and not self.retirement['enabled'] and not self.research['enabled'] \
            and not self.events['enabled'] and not self.dorm['enabled'] and not self.academy['enabled']:
            Logger.log_error("All modules are disabled, consider checking your config.")
            self.ok = False

        if self.updates['enabled']:
            if self.updates['channel'] != 'Release' and self.updates['channel'] != 'Development':
                self.ok = False
                Logger.log_error("Invalid update channel, please check the wiki.")

        if self.combat['enabled']:
            map = self.combat['map'].split('-')
            valid_chapters = list(range(1, 14)) + ['E']
            valid_levels = list(range(1, 5)) + ['A1', 'A2', 'A3', 'A4',
                                                'B1', 'B2', 'B3', 'B4',
                                                'C1', 'C2', 'C3', 'C4',
                                                'D1', 'D2', 'D3', 'D4',
                                                'SP1', 'SP2', 'SP3', 'SP4', 'SP5']
            if (self.try_cast_to_int(map[0]) not in valid_chapters or
                self.try_cast_to_int(map[1]) not in valid_levels):
                self.ok = False
                Logger.log_error("Invalid Map Selected: '{}'."
                                .format(self.combat['map']))

            if not isinstance(self.combat['oil_limit'], int):
                self.ok = False
                Logger.log_error("Oil limit must be an integer.")

            if not isinstance(self.combat['retire_cycle'], int) or self.combat['retire_cycle'] <= 0:
                self.ok = False
                Logger.log_error("RetireCycle must be an integer > 0.")

            if map[0] != "E" and self.combat['siren_elites']:
                self.ok = False
                Logger.log_error("Story maps don't have elite units.")

            if not isinstance(self.combat['kills_before_boss'], int) or self.combat['kills_before_boss'] < 0:
                self.ok = False
                Logger.log_error("Invalid KillsBeforeBoss value: must be an integer >= 0.")

            if not isinstance(self.combat['retreat_after'], int) or self.combat['retreat_after'] < 0:
                self.ok = False
                Logger.log_error("Invalid RetreatAfter value: must be an integer >= 0.")

            if map[0] != "E" and self.combat['small_boss_icon']:
                self.ok = False
                Logger.log_error("Story maps don't have small boss icon.")

            if not isinstance(self.combat['low_mood_sleep_time'], float) or self.combat['low_mood_sleep_time'] < 0:
                self.ok = False
                Logger.log_error("LowMoodSleepTime must be a float > 0.")

            if self.combat['search_mode'] not in [0, 1]:
                self.ok = False
                Logger.log_error("Wrong search mode. Allowed values: [0, 1].")

        if self.academy['enabled']:
            tier = self.academy['skill_book_tier']
            if not isinstance(tier, int) or not 1 <= tier <= 3:
                Logger.log_error("Skill book tier must be an integer between 1 and 3.")

        if self.events['enabled']:
            events = ['Crosswave', 'Royal_Maids']
            stages = ['EX', 'H', 'N', 'E']
            if self.events['name'] not in events or all(elem not in stages for elem in self.events['levels']):
                self.ok = False
                Logger.log_error("Invalid event settings, please check the wiki.")

        if self.retirement['enabled']:
            if not (self.retirement['commons'] or self.retirement['rares']):
                Logger.log_error("Retirement is enabled, but no ship rarities are selected.")
                self.ok = False

        if self.research['enabled']:
            if not (self.research['30Minutes'] or self.research['1Hour'] or self.research['1Hour30Minutes'] or self.research['2Hours'] or self.research['2Hours30Minutes'] or self.research['4Hours'] or self.research['5Hours'] or self.research['6Hours'] or self.research['8Hours'] or self.research['12Hours']):
                Logger.log_error("Research is enabled, but without allowed times.")
                self.ok = False

    def _rollback_config(self, config):
        """Method to roll back the config to the passed in config's.
        Args:
            config (dict): previously backed up config
        """
        for key in config:
            setattr(self, key, config['key'])

    def _validate_list(self, val, min_len=None, max_len=None, valid_vals=None, map_vals=None, cast=None, unique=False):
        s_list = re.split(r'\s*,\s*|\s+', val)

        if min_len is not None and len(s_list) < min_len:
            raise ValueError()
        if max_len is not None and len(s_list) > max_len:
            raise ValueError()
        if s_list is not None:
            for i in range(len(s_list)):
                s_list[i] = cast(s_list[i])
        if valid_vals is not None:
            for v in s_list:
                if v not in valid_vals:
                    raise ValueError()
                if map_vals is not None:
                    s_list[i] = map_vals[valid_vals.index(s_list[i])]
        if unique and len(set(s_list)) != len(s_list):
            raise ValueError()

        return s_list
