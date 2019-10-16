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

from h3m.manager import Manager, Match, Player, Database
from h3m.utils import MultilineFormatter, KeyStop

# folders
managerfolder = os.path.abspath(os.path.dirname(__file__))

# default database
default_db_filename = os.path.join(managerfolder, 'bots/db.sqlite3')


class Commandline:
    def __init__(self):
        self.cmds = None
        self.parser = argparse.ArgumentParser()
        self.no_args = False

        self.parser.add_argument('-v', action='count',
                                 default=0, dest='verbosity',
                                 help = "Make manager output more verbose")

        ##########
        # Bot handling
        self.parser.add_argument("-A", dest="add_bot",
                                 nargs=2, action = "store", default=[None],
                                 help = "Add a new bot with: NAME 'PATH'")

        self.parser.add_argument("-b", dest="play_bot",
                                 action = "store", default = None,
                                 help = "Specify bot to play in every match")

        self.parser.add_argument("-D", dest="delete_bot",
                                 action = "store", default = "",
                                 help = "Delete the named bot")

        self.parser.add_argument("-a", dest="activate_bot",
                                 action = "store", default = "",
                                 help = "Activate the named bot")

        self.parser.add_argument("-d", dest="deactivate_bot",
                                 action = "store", default = "",
                                 help = "Deactivate the named bot")

        self.parser.add_argument('--edit', dest = 'edit_bot',
                                 nargs=2, action = 'store', default = [None],
                                 help = "Edit the path of a bot with: NAME 'NEWPATH'")

        self.parser.add_argument('-rb', dest="reset_bot", action="store", default = None,
                                 help = "Reset a bot's record")

        self.parser.add_argument("--activateAll", dest="activate_all",
                                 action="store_true", default=False,
                                 help="Activate all bots")

        self.parser.add_argument("--deactivateAll", dest="deactivate_all",
                                 action="store_true", default=False,
                                 help="Deactivate all bots")

        ##########
        # Halite options
        self.parser.add_argument('-p', dest='player_dist',
                                 nargs='*', action='store', default=[2,4], type=int,
                                 help='Specify a custom distribution of players per match: {2,2,4}')

        self.parser.add_argument('-M', dest = 'map_dist', type = int,
                                nargs ='*', action = 'store', default=None,
                                help = 'Specify a custom distribution of (square) map sizes: {32,32,40,48}')

        self.parser.add_argument("-W", dest="map_width",
                                 action='store', default=0, type=int,
                                 help="Map width")

        self.parser.add_argument("-H", dest="map_height",
                                 action='store', default=0, type=int,
                                 help="Map height")

        self.parser.add_argument("-t", dest="turn_limit",
                                 action = "store", default = None, type=int,
                                 help = "Set match turn limit")

        self.parser.add_argument("-nt", dest="no_timeout",
                                 action = "store_true", default = False,
                                 help = "Do not apply turn timeouts")

        self.parser.add_argument("-s", dest="map_seed",
                                 action='store', default=0, type=int,
                                 help = "Map seed")

        ##########
        # Match handling
        self.parser.add_argument("-m", dest="match",
                                 action = "store_true", default = False,
                                 help = "Run a single match")

        self.parser.add_argument("-mm", dest="matches",
                                 action = "store", default=0, type=int,
                                 help = "Run number of matches")

        self.parser.add_argument("-f", dest="forever",
                                 action = "store_true", default = False,
                                 help = "Run games forever (or until interrupted)")

        self.parser.add_argument("-e", dest="equal_priority",
                                 action = "store_true", default = False,
                                 help = "Equal chance to play bots (DO NOT prioritize by sigma)")

        ##########
        # Feedback
        self.parser.add_argument("-r", dest="show_ranks",
                                 action="store_true", default=False,
                                 help="Show a list of all bots, ordered by skill")

        self.parser.add_argument("-E", dest="exclude_inactive",
                                 action = "store_true", default = None,
                                 help = "Exclude inactive bots from ranking table")

        self.parser.add_argument("-F", dest="view_file",
                                 action = "store", default = "",
                                 help = "View a replay file")

        self.parser.add_argument("-V", dest="view",
                                 action = "store", default = None,
                                 help = "View a replay from the database")

        self.parser.add_argument("-R", dest="results",
                                 action = "store", default = "",
                                 help = "View latest results starting from offset")

        self.parser.add_argument("-L", dest="limit",
                                 action = "store", default = "10",
                                 help = "Specify number of displayed results")

        ##########
        # Log handling
        self.parser.add_argument("-nr", dest="delete_replays",
                                 action = "store_true", default = False,
                                 help = "Do not store replays")

        self.parser.add_argument("-nl", dest="delete_logs",
                                 action = "store_true", default = False,
                                 help = "Do not store logs")

        self.parser.add_argument('--clear', dest="clear_old", action="store_true", default=False,
                                 help="Delete old replay and log files in replay directory")

        ##########
        # Database handling
        self.parser.add_argument('-db', dest='db_filename',
                                 action = "store", default = default_db_filename,
                                 help = 'Specify the database filename')

        self.parser.add_argument('--config', dest='config',
                                 action = "store_true", default = False,
                                 help="View the databases configuration.")

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
            h.setFormatter(MultilineFormatter("%(levelno)d:%(filename)s:line #%(lineno)d:%(message)s"))
        else:
            h.setFormatter(MultilineFormatter("%(message)s"))
        # logger = Manager.logger
        # logger.addHandler(h)
        # logger.setLevel(verbosity)

        self.manager = Manager(self.cmds.db_filename)

        # Clear logs, etc
        if self.cmds.clear_old:
            record_dir = self.manager.record_dir

            import glob
            print(f"Deleting replays (*.hlt) and logs (*.log) from:\n'{os.path.abspath(record_dir)}' and '{os.path.abspath(os.getcwd())}'")
            for fl in glob.glob(os.path.join(record_dir, "*.log")):
                os.remove(fl)
            for fl in glob.glob(os.path.join(record_dir, "*.hlt")):
                os.remove(fl)
            for fl in glob.glob(os.path.join(os.getcwd(), "*.log")):
                os.remove(fl)

        # Show config options
        if self.cmds.config:
            _, replays, halite, vis = self.manager.db.get_options()[0]
            print(f"Replay directory: '{replays}'\nHalite comand: '{halite}'\nVisualizer command: '{vis}'")

        # Change config options
        if self.cmds.halite:
            self.manager.set_halite_cmd(self.cmds.halite)
            print(f"Setting halite command to '{self.cmds.halite}'")
        if self.cmds.visualizer:
            self.manager.set_visualizer_cmd(self.cmds.visualizer)
            print(f"Setting visualizer command to '{self.cmds.visualizer}'")
        if self.cmds.replay_dir:
            self.manager.set_replay_dir(self.cmds.replay_dir)
            print(f"Setting replay directory to '{self.cmds.replay_dir}'")

        # View match file
        if self.cmds.view_file:
            print("Viewing replay file %s" %(self.cmds.view_file))
            self.manager.view_replay(self.cmds.view_file)

        # Reset database
        if self.cmds.reset:
            print('You want to reset the database.  This is IRRECOVERABLE.  Make a backup first.')
            print('This is equivalent to resetting every bot in the database.')
            print('Again, this CANNOT BE UNDONE.')
            ok = input('Continue? (y): ')
            if ok.lower() in ['y', 'yes']:
                self.manager.db.reset(self.cmds.db_filename)
                print('Database reset completed.')
            else:
                print('Database reset aborted. No changes made.')

        # Handle bots
        if self.cmds.add_bot[0]:
            print("Adding new bot...")
            bot_path = self.cmds.add_bot[1]
            if bot_path == "":
                print("You must specify the path for the new bot")
            elif self.valid_botfile(bot_path):
                self.manager.add_player(self.cmds.add_bot[0], bot_path)
        elif self.cmds.edit_bot[0]:
            bot_path = self.cmds.edit_bot[1]
            if not bot_path:
                print("You must specify the new path for the bot")
            elif self.valid_botfile(bot_path):
                self.manager.edit_path(self.cmds.edit_bot[0], bot_path)
        elif self.cmds.delete_bot:
            bot = self.cmds.delete_bot
            print(f"You want to delete player '{bot}'.  This is IRRECOVERABLE.")
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.delete_player(bot)
                print(f"Bot '{bot}' deleted.")
            else:
                print('Bot delete aborted. No changes made.')
        elif self.cmds.activate_bot:
            print("Activating bot '%s'" %(self.cmds.activate_bot))
            self.manager.db.activate_player(self.cmds.activate_bot)
        elif self.cmds.activate_all:
            print(f"You want to activate all bots. This CANNOT BE UNDONE.")
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.activate_all()
                print("All bots activated.")
            else:
                print('No changes made.')
        elif self.cmds.deactivate_bot:
            print("Deactivating bot '%s'" %(self.cmds.deactivate_bot))
            self.manager.db.deactivate_player(self.cmds.deactivate_bot)
        elif self.cmds.deactivate_all:
            print(f"You want to deactivate all bots. This CANNOT BE UNDONE.")
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.deactivate_all()
                print("All bots deactivated.")
            else:
                print('No changes made.')
        elif self.cmds.reset_bot:
            bot = self.cmds.reset_bot
            print(f"You want to reset player '{bot}'.  This is IRRECOVERABLE.")
            print('A new, scratch player with the same name and path will be created in its place.')
            ok = input('Continue?: ')
            if ok.lower() in ['y', 'yes']:
                self.manager.db.reset_player(bot)
                print(f"Bot '{bot}' reset completed.")
            else:
                print('Bot reset aborted. No changes made.')

        # Handle logs
        if self.cmds.delete_replays:
            print("keep_replays = False")
            self.manager.keep_replays = not self.cmds.delete_replays
        if self.cmds.delete_logs:
            print("keep_logs = False")
            self.manager.keep_logs = not self.cmds.delete_logs

        # Set match conditions
        if self.cmds.no_timeout:
            print("no_timeout = True")
        if self.cmds.equal_priority:
            print("priority_sigma = False")
            self.cmds.priority_sigma = not self.cmds.equal_priority
        if self.cmds.turn_limit:
            print("turn_limit = %d" % (self.cmds.turn_limit))

        # Match handling
        if self.cmds.play_bot:
            self.cmds.force = self.cmds.play_bot
            player = Player.parse_player_record(self.manager.db.get_player(self.cmds.play_bot)[0])
            if player:
                print(f"Playing '{self.cmds.play_bot}' @'{player.path}'")
            else:
                print(f"Player '{self.cmds.play_bot}' not in database. Ignoring request.")

        if self.cmds.match or self.cmds.matches or self.cmds.forever:
            if not self.cmds.forever and (not self.cmds.match and self.cmds.matches == 0):
                print(f"ValueError: '{self.cmds.matches}' is not a valid number of matches.")

            if self.cmds.map_seed:
                print(f"map_seed = {self.cmds.map_seed}")

            if self.cmds.map_width or self.cmds.map_height:
                width = self.cmds.map_width or self.cmds.map_height
                height = self.cmds.map_height or width
                self.cmds.map_width, self.cmds.map_height = width, height
                print(f"map size = {width}x{height}")
            else:
                print('map_dist = %s' % str(self.cmds.map_dist))

            print('player_dist = %s' % str(self.cmds.player_dist))

        if self.cmds.match:
            print("Running 1 round.")
            self.manager.run_rounds(1, progress_bar=False, **vars(self.cmds))
        elif self.cmds.matches:
            try:
                print(f"Running {self.cmds.matches} round(s). Press <q> to stop safely.")
                self.manager.run_rounds(self.cmds.matches, progress_bar=True, **vars(self.cmds))
            except KeyStop:
                pass
        elif self.cmds.forever:
            print(f"Running rounds forever. Press <q> to stop safely.")
            self.manager.run_rounds(-1, progress_bar=True, **vars(self.cmds))
        elif self.cmds.matches == 0:
            pass
        else:
            raise ValueError(f"Unhandled value for matches {type(self.cmds.matches)} {self.cmds.matches}")

        # Handle showing results/ranks
        if self.cmds.show_ranks:
            print('\n'+Player.get_columns())
            sql = "select * from players where active > 0 order by skill desc" if self.cmds.exclude_inactive else "select * from players order by skill desc"
            for p in self.manager.db.retrieve(sql):
                print(Player.parse_player_record(p))

        if self.cmds.results:
            print("\nDisplaying latest %s results from offset %s" %(self.cmds.limit, self.cmds.results))
            results = self.manager.db.get_results(self.cmds.results, self.cmds.limit)
            print("Match\tBots\t\tPlace/Halite\t\tW   H\tSeed\t\tTime\t\tReplay File")
            for result in results:
                print(result)

        # View replay by match
        if self.cmds.view is not None:
            self.cmds.view = int(self.cmds.view)
            id, filename = self.manager.get_replay_filename(self.cmds.view)
            if filename is None:
                print("Replay file missing")
                return
            elif filename != "No Replay Was Stored":
                self.manager.view_replay(filename)
            print(f"\nViewing replay for Match {id} -- {filename}")


if __name__ == '__main__':
    cmd = Commandline()
    cmd.parse(sys.argv[1:])
    cmd.act()
