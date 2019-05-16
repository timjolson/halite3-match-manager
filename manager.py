#!/usr/bin/env python3
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#      Unless required by applicable law or agreed to in writing, software
#      distributed under the License is distributed on an "AS IS" BASIS,
#      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#      See the License for the specific language governing permissions and
#      limitations under the License.

import os
import sys
import argparse
import logging

from halite.manager import Manager, Match, Player, Database
from halite.utils import MultilineFormatter, KeyStop

# folders
managerfolder = os.path.abspath(os.path.dirname(__file__))

# default database
db_filename = os.path.join(managerfolder, 'bots/db.sqlite3')


class Commandline:
    def __init__(self):
        self.cmds = None
        self.parser = argparse.ArgumentParser()
        self.no_args = False
        self.total_players = 0

        self.parser.add_argument('-v', action='count',
                                 default=0, dest='verbosity',
                                 help = "Make manager output more verbose")

        ##########
        # Bot handling
        self.parser.add_argument("-A", "--addBot", dest="addBot",
                                 nargs=2, action = "store", default=[None],
                                 help = "Add a new bot with: NAME 'PATH'")

        self.parser.add_argument("-D", "--deleteBot", dest="deleteBot",
                                 action = "store", default = "",
                                 help = "Delete the named bot")

        self.parser.add_argument("-a", "--activateBot", dest="activateBot",
                                 action = "store", default = "",
                                 help = "Activate the named bot")

        self.parser.add_argument("-d", "--deactivateBot", dest="deactivateBot",
                                 action = "store", default = "",
                                 help = "Deactivate the named bot")

        self.parser.add_argument('--edit', dest = 'editBot',
                                 nargs=2, action = 'store', default = [None],
                                 help = "Edit the path of a bot with: NAME 'NEWPATH'")

        self.parser.add_argument('-rb', dest="resetBot", action="store", default = None,
                                 help = "Reset a bot's record")

        self.parser.add_argument("--activateAll", dest="activateAll",
                                 action="store_true", default=False,
                                 help="Activate all bots")

        self.parser.add_argument("--deactivateAll", dest="deactivateAll",
                                 action="store_true", default=False,
                                 help="Deactivate all bots")

        self.parser.add_argument("-b", "--bot", dest="playBot",
                                 action = "store", default = None,
                                 help = "Specify bot to play in every match")

        ##########
        # Halite options
        self.parser.add_argument("-s", "--seed", dest="map_seed",
                                 action='store', default=0, type=int,
                                 help = "Map seed")

        self.parser.add_argument('-p', '--players', dest='player_dist',
                                 nargs='*', action='store', default=[2,4], type=int,
                                 help='Specify a custom distribution of players per match: {2,2,4}')

        self.parser.add_argument('--maps', dest = 'map_dist', type = int,
                                nargs ='*', action = 'store', default=None,
                                help = 'Specify a custom distribution of (square) map sizes: {32,32,40,48}')

        self.parser.add_argument("-W", "--Width", dest="map_width",
                                 action='store', default=0, type=int,
                                 help="Map width")

        self.parser.add_argument("-H", "--Height", dest="map_height",
                                 action='store', default=0, type=int,
                                 help="Map height")

        self.parser.add_argument("-t", "--turnLimit", dest="turnLimit",
                                 action = "store", default = None, type=int,
                                 help = "Set match turn limit")

        self.parser.add_argument("-nt", "--no-timeout", dest="noTimeout",
                                 action = "store_true", default = False,
                                 help = "Do not apply turn timeouts")

        ##########
        # Match handling
        self.parser.add_argument("-m", "--match", dest="match",
                                 action = "store_true", default = False,
                                 help = "Run a single match")

        self.parser.add_argument("-mm", "--matches", dest="matches",
                                 action = "store", default=0, type=int,
                                 help = "Run number of matches")

        self.parser.add_argument("-f", "--forever", dest="forever",
                                 action = "store_true", default = False,
                                 help = "Run games forever (or until interrupted)")

        self.parser.add_argument("-e", "--equal-priority", dest="equalPriority",
                                 action = "store_true", default = False,
                                 help = "Equal priority for all active bots (otherwise highest sigma will always be selected)")

        ##########
        # Feedback
        self.parser.add_argument("-r", "--showRanks", dest="showRanks",
                                 action="store_true", default=False,
                                 help="Show a list of all bots, ordered by skill")

        self.parser.add_argument("-E", "--exclude-inactive", dest="excludeInactive",
                                 action = "store_true", default = None,
                                 help = "Exclude inactive bots from ranking table")

        self.parser.add_argument("-F", "--viewfile", dest="viewfile",
                                 action = "store", default = "",
                                 help = "View a replay from a file")

        self.parser.add_argument("-V", "--view", dest="view",
                                 action = "store", default = None,
                                 help = "View a replay from the replay_dir")

        self.parser.add_argument("-R", "--results", dest="results",
                                 action = "store", default = "",
                                 help = "View results starting from offset")

        self.parser.add_argument("-L", "--limit", dest="limit",
                                 action = "store", default = "10",
                                 help = "Limit number of displayed results")

        ##########
        # Log handling
        self.parser.add_argument("-n", "--no-replays", dest="deleteReplays",
                                 action = "store_true", default = False,
                                 help = "Do not store replays")

        self.parser.add_argument("-l", "--no-logs", dest="deleteLogs",
                                 action = "store_true", default = False,
                                 help = "Do not store logs")

        self.parser.add_argument('--clear', dest="clear_old", action="store_true", default=False,
                                 help="Delete old replay and log files in replay directory")

        ##########
        # Database handling
        self.parser.add_argument('-db', dest='db_filename',
                                 action = "store", default = db_filename,
                                 help = 'Specify the database filename')

        self.parser.add_argument('--reset', dest='reset',
                                 action = 'store_true', default = False,
                                 help = 'Delete ALL information in the database, then recreate a new one with existing bot names and paths')

        self.parser.add_argument('--replay_dir', dest='replay_dir',
                                 action = "store", default = None,
                                 help = 'Specify the replay storage directory')

        self.parser.add_argument('--visualizer', dest='visualizer',
                                 action = "store", default = "",
                                 help="Specify the visualizer command string with: \"vis.exe -opt1 FILENAME opt2\"")

        self.parser.add_argument('--halite', dest='halite',
                                 action = "store", default = None,
                                 help="Specify the halite command string with: \"../halite/halite.exe\"")

        self.parser.add_argument('--config', dest='config',
                                 action = "store_true", default = False,
                                 help="View the databases configuration.")

    def parse(self, args):
        self.no_args = not args
        self.cmds = self.parser.parse_args(args)

    def valid_botfile(self, path):
        return True

    def act(self):
        if self.no_args:
            self.parser.print_help()
            return

        verbosity = max(logging.ERROR - self.cmds.verbosity * 10, 1)
        """
        logging.ERROR = 40
        logging.WARN = 30
        logging.INFO = 20
        logging.DEBUG = 10
        logging.NOTSET = 0
        """
        h = logging.StreamHandler(sys.stdout)
        if verbosity <= 10:
            h.setFormatter(MultilineFormatter("%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:%(message)s"))
        logger = Manager.logger
        logger.addHandler(h)
        logger.setLevel(verbosity)

        self.manager = Manager(self.cmds.db_filename)
        Match.logger = logger
        Database.logger = logger
        Player.logger = logger

        # Clear logs, etc
        if self.cmds.clear_old:
            record_dir = self.manager.record_dir

            import glob
            logger.error(f"Deleting replays (*.hlt) and logs (*.log) from:\n'{os.path.abspath(record_dir)}' and '{os.path.abspath(os.getcwd())}'")
            for fl in glob.glob(os.path.join(record_dir, "*.log")):
                os.remove(fl)
            for fl in glob.glob(os.path.join(record_dir, "*.hlt")):
                os.remove(fl)
            for fl in glob.glob(os.path.join(os.getcwd(), "*.log")):
                os.remove(fl)

        # Show config options
        if self.cmds.config:
            _, replays, halite, vis = self.manager.db.get_options()[0]
            logger.error(f"Replay directory: '{replays}'\nHalite comand: '{halite}'\nVisualizer command: '{vis}'")

        # Change config options
        if self.cmds.halite:
            self.manager.set_halite_cmd(self.cmds.halite)
        if self.cmds.visualizer:
            self.manager.set_visualizer_cmd(self.cmds.visualizer)
        if self.cmds.replay_dir:
            self.manager.set_replay_dir(self.cmds.replay_dir)

        # View match file
        if self.cmds.viewfile:
            logger.info("Viewing replay file %s" %(self.cmds.viewfile))
            self.manager.view_replay(self.cmds.viewfile)

        # Reset database
        if self.cmds.reset:
            logger.error('You want to reset the database.  This is IRRECOVERABLE.  Make a backup first.')
            logger.error('This is equivalent to resetting every bot in the database.')
            logger.error('Again, this CANNOT BE UNDONE.')
            ok = input('Continue? (y): ')
            if ok.lower() in ['y', 'yes']:
                self.manager.db.reset(self.cmds.db_filename)
                logger.error('Database reset completed.')
            else:
                logger.error('Database reset aborted. No changes made.')

        # Handle bots
        if self.cmds.addBot[0]:
            logger.error("Adding new bot...")
            botPath = self.cmds.addBot[1]
            if botPath == "":
                logger.error("You must specify the path for the new bot")
            elif self.valid_botfile(botPath):
                self.manager.add_player(self.cmds.addBot[0], botPath)
        elif self.cmds.editBot[0]:
            botPath = self.cmds.editBot[1]
            if not botPath:
                logger.error("You must specify the new path for the bot")
            elif self.valid_botfile(botPath):
                self.manager.edit_path(self.cmds.editBot[0], botPath)
        elif self.cmds.deleteBot:
            bot = self.cmds.deleteBot
            logger.error(f"You want to delete player '{bot}'.  This is IRRECOVERABLE.")
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.delete_player(self.cmds.deleteBot)
                logger.error(f"Bot '{bot}' deleted.")
            else:
                logger.error('Bot delete aborted. No changes made.')
        elif self.cmds.activateBot:
            logger.error("Activating bot %s" %(self.cmds.activateBot))
            self.manager.db.activate_player(self.cmds.activateBot)
        elif self.cmds.activateAll:
            logger.error(f"You want to activate all bots. This CANNOT BE UNDONE.")
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.activate_all()
                logger.error("All bots activated.")
            else:
                logger.error('No changes made.')
        elif self.cmds.deactivateBot:
            logger.error("Deactivating bot %s" %(self.cmds.deactivateBot))
            self.manager.db.deactivate_player(self.cmds.deactivateBot)
        elif self.cmds.deactivateAll:
            logger.error(f"You want to deactivate all bots. This CANNOT BE UNDONE.")
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.deactivate_all()
                logger.error("All bots deactivated.")
            else:
                logger.error('No changes made.')
        elif self.cmds.resetBot:
            bot = self.cmds.resetBot
            logger.error(f"You want to reset player '{bot}'.  This is IRRECOVERABLE.")
            logger.error('A new, scratch player with the same name and path will be created in its place.')
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.db.reset_player(bot)
                logger.error(f"Bot '{bot}' reset completed.")
            else:
                logger.error('Bot reset aborted. No changes made.')

        # Handle logs
        if self.cmds.deleteReplays:
            logger.debug("keep_replays = False")
            self.manager.keep_replays = False

        if self.cmds.deleteLogs:
            logger.debug("keep_logs = False")
            self.manager.keep_logs = False

        # Set match conditions
        if self.cmds.noTimeout:
            logger.debug("no_timeout = True")
            self.manager.no_timeout = True

        if self.cmds.turnLimit:
            self.manager.turn_limit = int(self.cmds.turnLimit) if self.cmds.turnLimit else None
            logger.info("Manual turn limit of %s" % (self.cmds.turnLimit))

        if self.cmds.equalPriority:
            logger.debug("priority_sigma = False")
            self.manager.priority_sigma = False

        # Match handling
        if self.cmds.playBot:
            self.manager.bot = self.cmds.playBot
            player = self.manager.get_player(self.cmds.playBot)
            if player:
                logger.error(f"Playing '{self.cmds.playBot}' @'{player.path}'")
            else:
                logger.error(f"Player '{self.cmds.playBot}' not in database. Ignoring request.")

        if self.cmds.match or self.cmds.matches:
            if not self.cmds.match and self.cmds.matches == 0:
                logger.critical(f"ValueError: '{self.cmds.matches}' is not a valid number of matches.")

            if self.cmds.map_seed:
                logger.debug(f"Using match seed {self.cmds.map_seed}")

            if self.cmds.map_width or self.cmds.map_height:
                width = self.cmds.map_width or self.cmds.map_height
                height = self.cmds.map_height or width
                self.cmds.map_width, self.cmds.map_height = width, height
                logger.debug(f"Using map size = {width}x{height}")
            else:
                logger.debug('Using map distribution %s' % str(self.cmds.map_dist))

            logger.debug('Using player distribution %s' % str(self.cmds.player_dist))

        if self.cmds.match:
            self.cmds.matches = 1
        if self.cmds.matches:
            try:
                self.manager.run_rounds(self.cmds.matches, self.cmds.player_dist, self.cmds.map_width, self.cmds.map_height,
                                        self.cmds.map_seed, self.cmds.map_dist, self.cmds.playBot, progress_bar=True)
            except KeyStop:
                pass
        elif self.cmds.forever:
            self.manager.run_rounds(-1, self.cmds.player_dist, self.cmds.map_width, self.cmds.map_height,
                                    self.cmds.map_seed, self.cmds.map_dist, self.cmds.playBot)

        # Handle showing results/ranks
        if self.cmds.showRanks:
            level = logger.getEffectiveLevel()
            logger.setLevel(logging.DEBUG)
            self.manager.show_ranks(self.cmds.excludeInactive)
            logger.setLevel(level)

        if self.cmds.results:
            level = logger.getEffectiveLevel()
            logger.setLevel(logging.DEBUG)
            logger.info("Displaying latest %s results from offset %s" %(self.cmds.limit, self.cmds.results))
            self.manager.show_results(self.cmds.results, self.cmds.limit)
            logger.setLevel(level)

        # View replay by match
        if self.cmds.view is not None:
            self.cmds.view = int(self.cmds.view)
            id, filename = self.manager.get_replay_filename(self.cmds.view)
            if filename != "No Replay Was Stored":
                self.manager.view_replay(filename)
            logger.error(f"Viewing replay for Match {id} :: {filename}")


if __name__ == '__main__':
    cmd = Commandline()
    cmd.parse(sys.argv[1:])
    cmd.act()
