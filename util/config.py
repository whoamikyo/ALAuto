import configparser
import sys
from copy import deepcopy
from util.logger import Logger


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
        self.events = {'enabled': False}
        self.network = {}
        self.assets = {}
        self.read()

    def read(self):
        backup_config = deepcopy(self.__dict__)
        config = configparser.ConfigParser()
        config.read(self.config_file)
        self.network['service'] = config.get('Network', 'Service')
        self.assets['server'] = config.get('Assets', 'Server')

        if config.getboolean('Updates', 'Enabled'):
            self._read_updates(config)

        if config.getboolean('Combat', 'Enabled'):
            self._read_combat(config)

        if config.getboolean('Headquarters', 'Dorm') or config.getboolean('Headquarters', 'Academy'):
            self._read_headquarters(config)

        self.commissions['enabled'] = config.getboolean('Modules', 'Commissions')
        self.enhancement['enabled'] = config.getboolean('Modules', 'Enhancement')
        self.missions['enabled'] = config.getboolean('Modules', 'Missions')
        
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

        if config.getboolean('Events', 'Enabled'):
            self._read_event(config)

        self.validate()
        if (self.ok and not self.initialized):
            Logger.log_msg("Starting ALAuto!")
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

    def _read_updates(self, config):
        """Method to parse the Combat settings of the passed in config.
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
        self.combat['boss_fleet'] = config.getboolean('Combat', 'BossFleet')
        self.combat['oil_limit'] = int(config.get('Combat', 'OilLimit'))
        self.combat['retire_cycle'] = int(config.get('Combat', 'RetireCycle'))
        self.combat['retreat_after'] = int(config.get('Combat', 'RetreatAfter'))
        self.combat['hide_subs_hunting_range'] = config.getboolean('Combat', 'HideSubsHuntingRange')
        self.combat['small_boss_icon'] = config.getboolean('Combat', 'SmallBossIcon')
        self.combat['siren_elites'] = config.getboolean('Combat', 'SirenElites')

    def _read_headquarters(self, config):
        """Method to parse the Headquarters settings passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.dorm['enabled'] = config.getboolean('Headquarters', 'Dorm')
        self.academy['enabled'] = config.getboolean('Headquarters', 'Academy')
        if self.academy['enabled']:
            self.academy['skill_book_tier'] = int(config.get('Headquarters', 'SkillBookTier'))

    def _read_event(self, config):
        """Method to parse the Event settings of the passed in config.
        Args:
            config (ConfigParser): ConfigParser instance
        """
        self.events['enabled'] = True
        self.events['name'] = config.get('Events', 'Event')
        self.events['levels'] = config.get('Events', 'Levels').split(',')
        self.events['ignore_rateup'] = config.getboolean('Events', 'IgnoreRateUp')

    def validate(self):
        def try_cast_to_int(val):
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
           and not self.missions['enabled'] and not self.retirement['enabled'] and not self.events['enabled']:
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
            if (try_cast_to_int(map[0]) not in valid_chapters or
                try_cast_to_int(map[1]) not in valid_levels):
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

            if map[0] != "E" and self.combat['small_boss_icon']:
                self.ok = False
                Logger.log_error("Story maps don't have small boss icon.")

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

    def _rollback_config(self, config):
        """Method to roll back the config to the passed in config's.
        Args:
            config (dict): previously backed up config
        """
        for key in config:
            setattr(self, key, config['key'])
