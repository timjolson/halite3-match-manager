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

import random
import os
import subprocess
import logging
import ast
from tqdm import tqdm

from halite.manager import match
from halite.manager import database
from halite.manager import player as pl
from halite.utils import keyboard_detection, KeyStop


class TerminatedException(Exception):
    pass


class Manager:
    def __init__(self, db_filename='/bots/db.sqlite3', verbosity=logging.DEBUG):
        self.bot = None
        self.players_min = 2
        self.players_max = 4
        self.player_dist = [2, 4]
        self.map_dist = [i*8 for i in range(4, 9)]
        self.rounds = -1
        self.round_count = 0
        self.keep_replays = True
        self.keep_logs = True
        self.no_timeout = False
        self.turn_limit = None
        self.priority_sigma = True
        self.exclude_inactive = False
        self.map_width, self.map_height, self.map_seed = None, None, None

        self.verbosity = verbosity
        self.logger = logging.getLogger()
        self.logger.setLevel(verbosity)

        self.refresh_db(db_filename)
        try:
            _, self.record_dir, self.halite_binary, vis_cmd = self.db.get_options()[0]
            self.visualizer_cmd = ast.literal_eval(vis_cmd)
        except ValueError:
            # no options set in db
            self.record_dir = ''
            self.halite_binary = ''
            self.visualizer_cmd = []

        self.logger.warning('Using database %s' % db_filename)

    def refresh_db(self, db_filename=None):
        if db_filename:
            db_filename=os.path.abspath(db_filename)
            if not os.path.exists(os.path.dirname(db_filename)):
                os.mkdir(os.path.dirname(db_filename))

        new_db = db_filename or self.db_filename
        self.db = None  # close database
        self.db = database.Database(new_db)
        self.db_filename = new_db

    def set_halite_cmd(self, cmd):
        self.logger.error(f"Setting halite command to '{cmd}'")
        self.halite_binary = cmd
        self.db.set_halite_cmd(cmd)

    def set_visualizer_cmd(self, cmd):
        self.logger.error(f"Setting visualizer command to '{cmd}'")
        self.visualizer_cmd = ast.literal_eval(cmd)
        self.db.set_visualizer_cmd(cmd)

    def set_replay_dir(self, dir):
        self.logger.error(f"Setting replay directory to '{dir}'")
        self.record_dir = dir
        self.db.set_replay_directory(dir)

    def activate_all(self):
        self.logger.warning("Activating all players...")
 #       for player in self.get_all_players():
 #           self.db.activate_player(player.name)
        player_records = self.db.retrieve("select * from players")
        players = [pl.Player.parse_player_record(player) for player in player_records]
        self.db.update_many("update players set active=? where name=?", [(1, p.name) for p in players])
        self.refresh_db()

    def deactivate_all(self):
        self.logger.warning("Deactivating all players...")
        self.db.update_many("update players set active=? where name=?", [(0, p.name) for p in self.get_all_players()])
        self.refresh_db()

    def match_callback(self, match):
        '''Match callback method.
        1. Adds match to database
        2. Saves players skills and ranks if non were terminated
        3. Shows ranks
        4. If any players were terminated, raises TerminatedException

        :param match: Match object of last played match
        '''
        self.db.add_match(match)

        if not any(match.terminated.values()):
            self.save_players(match.players)
            self.db.update_player_ranks()
            id, filename = self.db.get_replay_filename(0)
            self.logger.warning(f"\nMatch ID: {id} --- Seed: {match.map_seed} --- Size: {match.map_width}x{match.map_height}\nReplay file: {filename}")

            result = ''
            for pid, res in enumerate(match.results):
                name = match.players[pid].name
                rank, score = eval(res)
                result += f"{name:<16}:: Rank: {rank}  Score: {score}\n"
            self.logger.warning(result)

        else:
            msg = f"A bot was terminated: {match.terminated} \n{match.players}"
            self.logger.error(msg)
            raise TerminatedException(msg)

    def save_players(self, players):
        for player in players:
            self.logger.debug("Saving player %s with %f skill" % (player.name, player.skill))
            self.db.save_player(player)

    def pick_contestants(self, num, force=None):
        self.logger.debug(f"Picking {num} contestants")

        pool = list(self.get_all_players())
        contestants = list()
#        if self.priority_sigma:
#            high_sigma_index = max((player.sigma, i) for i, player in enumerate(self.players))[1]
#            high_sigma_contestant = self.players[high_sigma_index]
#            contestants.append(high_sigma_contestant)
#            pool.remove(high_sigma_contestant)
#            num -= 1
        if force is None:
            force = self.bot
        if force:
            self.logger.info(f"Forcing {force} to play")
            force = self.get_player(force)
            pool.remove(force)
            num -= 1
        random.shuffle(pool)
        contestants.extend(pool[:num])
        if force:
            contestants.append(force)
        random.shuffle(contestants)
        return contestants

    def run_rounds(self, nrounds=None, player_dist=None, map_dist=None, force=None):
        '''
        Run rounds.

        :param nrounds: int, number of rounds (-1:forever) to run
        :param player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        :param map_dist: [N,N,N], distribution of map size, e.g. [32,40,48,56,64]
        :return:
        '''
        if nrounds is None:
            nrounds = self.rounds

        try:
            # run unix
            with keyboard_detection() as key_pressed:
                while not key_pressed() and ((nrounds < 0) or (self.round_count < nrounds)):
                    self.setup_round(player_dist, map_dist, force)
        except ImportError:
            # run windows
            import msvcrt
            while not msvcrt.kbhit() and ((nrounds < 0) or (self.round_count < nrounds)):
                self.setup_round(player_dist, map_dist, force)

    def run_supervised_rounds(self, nrounds=None, player_dist=None, map_dist=None, force=None):
        '''
        Run rounds with progress bar, no keyboard stoppage.

        :param nrounds: int, number of rounds (-1:forever) to run
        :param player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        :param map_dist: [N,N,N], distribution of map size, e.g. [32,40,48,56,64]
        :return:
        '''
        if nrounds is None:
            nrounds = self.rounds

        if nrounds >= 0:
            with keyboard_detection() as key_pressed:
                pbar = tqdm(range(nrounds), leave=False, desc=f'Rounds', ncols=80)
                stopped = False
                for _ in range(nrounds):
                    if key_pressed():
                        stopped = True
                        break
                    self.setup_round(player_dist, map_dist, force)
                    pbar.update()
                pbar.close()
                if stopped or key_pressed():
                    raise KeyStop
        else:
            while True:
                self.setup_round(player_dist, map_dist, force)

    def setup_round(self, player_dist, map_dist, force=None):
        '''
        Select players and options for a match, then run it.

        :param player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        :param map_dist: [N,N,N], distribution of map size, e.g. [32,40,48,56,64]
        :return: match
        '''
        if player_dist is None:
            player_dist = self.player_dist
        if map_dist is None:
            map_dist = self.map_dist

        if self.players_max > 3:
            num_contestants = random.choice(player_dist)
        else:
            num_contestants = self.players_min
        contestants = self.pick_contestants(num_contestants, force=force)
        self.logger.debug('\n'.join([str(c) for c in contestants]))

        size_w = self.map_width or self.map_height or random.choice(map_dist)
        size_h = self.map_height or size_w
        seed = self.map_seed or random.randint(10000, 2073741824)

        match = self.run_single_round(contestants, size_w, size_h, seed)
        self.round_count += 1
        return match

    def run_single_round(self, contestants, width, height, seed):
        '''
        Create and run a Match. At end of match, self.match_callback(match) is called.

        :param contestants: iterable of player objects to compete
        :param width: map width
        :param height: map height
        :param seed: map seed
        :return: Match object
        '''
        self.logger.info("\n------------------- Running new match... -------------------\n")
        m = match.Match(contestants, width, height, seed, self.turn_limit, self.keep_replays,
                        self.keep_logs, self.no_timeout, self.record_dir, self.halite_binary)
        cont_str = '\n'.join([str(c) for c in contestants])
        self.logger.info(f"Contestants:\n{pl.Player.get_columns()}\n{cont_str}")
        try:
            m.run_match()
            self.match_callback(m)
        except TerminatedException as e:
            raise
        except Exception as e:
            import traceback
            self.logger.error(f"Exception in run_round:\n{traceback.format_exc()}")
            raise
        return m

    def get_player(self, name):
        player = self.db.get_player([name])[0]
        player = pl.Player.parse_player_record(player)
        return player

    def get_all_players(self):
        player_records = self.db.retrieve("select * from players where active > 0")
        players = [pl.Player.parse_player_record(player) for player in player_records]
        return players

    def add_player(self, name, path):
        p = self.db.get_player((name,))
        if len(p) == 0:
            self.db.add_player(name, path)
            self.logger.error(f"Bot '{name}' added to database at '{path}'")
        else:
            self.logger.error("Bot name %s ALREADY USED! No bot added" %(name))

    def delete_player(self, name):
        self.db.delete_player(name)

    def edit_path(self, name, path):
        p = self.db.get_player((name,))
        if not p:
            self.logger.error('Bot name %s NOT FOUND, no edits made' %(name))
        else:
            p = pl.Player.parse_player_record(p[0])
            self.logger.error("Updating path for bot '%s'" % (name))
            self.logger.error(f"From: '{p.path}'  to  '{path}'")
            self.db.update_player_path(name, path)

    def show_ranks(self, tsv=False):
        if tsv:
            self.logger.info("\n%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % ("name", "last_seen", "rank", "skill", "mu", "sigma", "ngames", "active"))
        else:
            self.logger.info('\n'+pl.Player.get_columns())
        sql = "select * from players where active > 0 order by skill desc" if self.exclude_inactive else "select * from players order by skill desc"
        for p in self.db.retrieve(sql):
            self.logger.info(pl.Player.parse_player_record(p))

    def show_results(self, offset, limit):
        results = self.db.get_results(offset, limit)
        self.logger.info("Match\tBots\t\tPlace/Halite\t\tW   H\tSeed\t\tTime\t\tReplay File")
        for result in results:
            self.logger.info(result)

    def get_replay_filename(self, id):
        id, filename = self.db.get_replay_filename(id)
        if filename == 'No Replay Was Stored':
            return id, filename
        elif os.path.isfile(filename):
            return id, filename
        else:
            self.logger.error(f"Replay was not found :: {filename}")
            return id, None

    def view_replay(self, filename):
        cmd = []
        valid = False
        for idx, value in enumerate(self.visualizer_cmd):
            if value.upper() == "FILENAME":
                cmd.append(filename)
                valid = True
            else:
                cmd.append(value)
        if cmd and valid:
            self.logger.debug(f"Vis command = \"{cmd}\"")
            subprocess.Popen(cmd)
        else:
            raise ValueError(f"Visualizer command '{self.visualizer_cmd}' invalid.")
