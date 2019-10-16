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
import skills
from skills import trueskill

from .match import Match
from .database import Database
from .player import Player
from h3m.utils import keyboard_detection, KeyStop


class TerminatedException(Exception):
    pass


class Manager:
    """
    Halite Match Manager.

    Manager('path/to/database/file')
    """
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())

    def __init__(self, db_filename, **kwargs):
        '''
        # kwargs accepts:
        force: str, name of bot to force into playing
        priority_sigma: bool, whether to prioritize bots by their sigma rating

        player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        players_min: int, min players in a game
        players_max: int, max players in a game

        map_dist: [N,N,N], distribution of map size (overridden if a dimension specified)
        map_width: int, map units in width
        map_height: int, map units in height
        map_seed: int, seed for halite executable to use when generating maps, etc.

        rounds: int, number of rounds to run in .run_matches()
        turn_limit: int, number of maximum turns in a single round
        no_timeout: bool, run halite without per-turn timeout

        keep_logs: bool, keep halite logs
        keep_replays: bool, keep replay files

        # These settings normally stored in database.
        # Passing them in kwargs DOES NOT change the database.
        # To change the database, use .set_halite_cmd / .set_visualizer_cmd / .set_replay_dir
        record_dir: str, directory to store replays and halite log
        halite_binary: str, path to halite executable
        visualizer_cmd: str, command to run vizualizer
        '''
        self.players_min = kwargs.pop('players_min', 2)
        self.players_max = kwargs.pop('players_max', 4)
        self.player_dist = kwargs.pop('player_dist', [2, 4])
        self.map_dist = kwargs.pop('map_dist', [i*8 for i in range(4, 9)])
        self.rounds = kwargs.pop('rounds', -1)
        self.keep_replays = kwargs.pop('keep_replays', True)
        self.keep_logs = kwargs.pop('keep_logs', True)
        self.no_timeout = kwargs.pop('no_timeout', False)
        self.turn_limit = kwargs.pop('turn_limit', None)
        self.priority_sigma = kwargs.pop('priority_sigma', True)
        self.force = kwargs.pop('force', None)
        self.map_width = kwargs.pop('map_width', None)
        self.map_height = kwargs.pop('map_height', None)
        self.map_seed = kwargs.pop('map_seed', None)

        self.reload_db(db_filename)
        try:
            _, rd, hb, vc = self.db.get_options()[0]
        except ValueError:
            # no options set in db
            rd, hb, vc = None, None, None

        # override config for this instance
        self.record_dir = rd or kwargs.pop('record_dir', '')
        self.halite_binary = hb or kwargs.pop('halite_binary', '')
        self.visualizer_cmd = vc or kwargs.pop('visualizer_cmd', '')

        if kwargs:
            raise ValueError(f"Unexpected kwargs {kwargs}")

    def reload_db(self, db_filename=None):
        """
        Close currently open database and re-open it (or open new provided db).
        :param db_filename: str, path to database
        :return:
        """
        if db_filename:
            db_filename=os.path.abspath(db_filename)
            if not os.path.exists(os.path.dirname(db_filename)):
                os.mkdir(os.path.dirname(db_filename))

        new_db = db_filename or self.db_filename

        self.db = None  # close database
        self.db = Database(new_db)
        self.db_filename = new_db

    def set_halite_cmd(self, cmd):
        """
        Change command to run halite executable. Entered into database.
        :param cmd: str, command to run halite executable
        :return:
        """
        self.halite_binary = cmd
        self.db.set_halite_cmd(cmd)

    def set_visualizer_cmd(self, cmd):
        """
        Change command to run for visualizing a replay.
        FILENAME will be replaced with each usage.
        :param cmd: str, e.g. "executable option FILENAME option"
        :return:
        """
        self.visualizer_cmd = cmd
        self.db.set_visualizer_cmd(cmd)

    def set_replay_dir(self, dir):
        """
        Change directory to store replays in. Entered into database.
        :param dir: str, directory
        :return:
        """
        self.record_dir = dir
        self.db.set_replay_directory(dir)

    def activate_all(self):
        """
        Activate all bots in database.
        :return:
        """
        player_records = self.db.retrieve("select * from players")
        players = [Player.parse_player_record(player) for player in player_records]
        self.db.update_many("update players set active=? where name=?", [(1, p.name) for p in players])

    def deactivate_all(self):
        """
        Deactivate all bots in database.
        :return:
        """
        self.db.update_many("update players set active=? where name=?", [(0, p.name) for p in self.db.get_active_players()])

    def update_skills(self, players, ranks):
        """ Update player skills based on ranks from a match """
        teams = [skills.Team({player.name: skills.GaussianRating(player.mu, player.sigma)}) for player in players]
        match = skills.Match(teams, ranks)
        calc = trueskill.FactorGraphTrueSkillCalculator()
        game_info = trueskill.TrueSkillGameInfo()
        game_info.dynamics_factor = 0.2
        updated = calc.new_ratings(match, game_info)
        for team in updated:
            player_name, skill_data = next(iter(team.items()))  # in Halite, teams will always be a team of one player
            player = next(player for player in players if player.name == str(
                player_name))  # this suggests that players should be a dictionary instead of a list
            player.mu = skill_data.mean
            player.sigma = skill_data.stdev
            player.update_skill()

    def match_callback(self, match):
        """
        Post-match callback.
        Does the following:
        1. Adds match to database
        2. Saves players' new skills and ranks if none were terminated
        3. Show post-match bot ranks
        4. If any players were terminated, raises TerminatedException
        """
        self.db.add_match(match)

        if not any(match.terminated.values()):
            results = [ast.literal_eval(mr) for mr in match.results]  # get tuple from strings stored in database
            self.update_skills(match.players, [i[0] for i in results])  # tuple ~ (rank, halite)
            for pl in match.players:
                self.db.save_player(pl)
            self.db.update_player_ranks()  # update all player ranks
            id, filename = self.db.get_replay_filename(0)
            # self.logger.debug(f"Match ID: {id} -- Seed: {match.map_seed} -- Size: {match.map_width}x{match.map_height}\nReplay: '{filename}'")

            result = ''
            for pid, res in enumerate(results):
                name = match.players[pid].name
                rank, score = res
                result += f"{name:<10} -- Rank: {rank} -- Score: {score}\n"
            # self.logger.debug(result)

        else:
            msg = f"A bot was terminated: {match.terminated}\n{[p.name for p in match.players]}"
            raise TerminatedException(msg)

    def pick_contestants(self, num, force=None, priority_sigma=None):
        """
        Pick contestants to compete in a match.
        :param num: int, total number of competitors for match
        :param force: str, name of bot to force play
        :param priority_sigma: bool, whether to prioritize bots by their sigma rating
        :return: [Players]
        """
        if priority_sigma is None:
            priority_sigma = self.priority_sigma
        if force is None:
            force = self.force

        pool = list(self.db.get_active_players())
        contestants = list()
        if force:
            force = [pl for pl in pool if pl.name == force][0]
            # force = self.db.get_player(force)[0]
            pool.remove(force)
            contestants.append(force)
            num -= 1
        if priority_sigma:
            high_sigma_index = max((player.sigma, i) for i, player in enumerate(pool))[1]
            high_sigma_contestant = pool[high_sigma_index]
            pool.remove(high_sigma_contestant)
            contestants.append(high_sigma_contestant)
            num -= 1
        random.shuffle(pool)
        contestants.extend(pool[:num])
        random.shuffle(contestants)
        return contestants

    def run_rounds(self, nrounds=None, **kwargs):
        """
        Run a number of rounds. Configures then runs multiple matches, calling match_callback on each.

        :param nrounds: int, number of rounds to run (-1=forever)
        NOTE: any argument can accept `None` to use the Manager's already configured setting

        kwargs accepts:
        progress_bar: bool, whether to display progress bar while running
        player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        map_width: int, map units in width
        map_height: int, map units in height
        map_dist: [N,N,N], distribution of map size (overridden if a dimension specified)
                    e.g. [32,40,48,56,64]
        map_seed: int, seed for halite executable to use when generating maps, etc.
        force: str, name of bot to force into playing
        turn_limit: int, number of maximum turns in a single round
        no_timeout: bool, run halite without per-turn timeout
        priority_sigma: bool, whether to prioritize bots by their sigma rating
        keep_logs: bool, keep halite logs
        keep_replays: bool, keep replay files
        record_dir: str, directory to store replays and halite logs
        halite_binary: str, path to halite executable
        :return:
        """
        if nrounds is None:
            nrounds = self.rounds
        if nrounds == 0:
            raise ValueError(f"'{nrounds}' is not a valid number of matches.")

        try:
            # run unix
            with keyboard_detection() as key_pressed:
                self._run_deferred(key_pressed, nrounds, **kwargs)
        except ImportError:
            # run windows
            import msvcrt
            self._run_deferred(msvcrt.kbhit, nrounds, **kwargs)

    def _run_deferred(self, key_pressed, nrounds=None, **kw):
        inf = (nrounds == -1)
        # self.logger.debug(
        #     f"Running {'ENDLESS' if inf is True else nrounds} match(es), or until interrupted. Press <q> or <ESC> key to exit safely.")

        kw.setdefault('progress_bar', False)
        self._apply_default_settings(kw)

        progress_bar = ((nrounds > 1) and kw['progress_bar']) or (nrounds == -1 and kw['progress_bar'])
        stopped = False

        # N rounds, with progress bar
        if progress_bar is True:
            if inf:
                pbar = tqdm(leave=True, desc='Rounds', ncols=80)
                while not key_pressed():
                    m = self.configure_match(**kw)
                    self.run_match(m)
                    pbar.update()
            else:
                pbar = tqdm(range(nrounds), leave=False, desc='Rounds', ncols=80)
                for _ in range(nrounds):
                    if key_pressed():
                        stopped = True
                        break
                    m = self.configure_match(**kw)
                    self.run_match(m)
                    pbar.update()
                pbar.close()
                if stopped is True or key_pressed():
                    raise KeyStop()
        else:
            # infinite rounds
            if inf:
                while not key_pressed():
                    m = self.configure_match(**kw)
                    self.run_match(m)

            # N rounds
            else:
                for _ in range(nrounds):
                    if key_pressed():
                        stopped = True
                        break
                    m = self.configure_match(**kw)
                    self.run_match(m)
                if stopped is True or key_pressed():
                    raise KeyStop()

    def configure_match(self, **kwargs):
        """
        Select players (from database) and options
            (will use configured defaults) for a match.

        kwargs accepts:
        player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        map_width: int, map units in width
        map_height: int, map units in height
        map_dist: [N,N,N], distribution of map size (overridden if a dimension specified)
                    e.g. [32,40,48,56,64]
        map_seed: int, seed for halite executable to use when generating maps, etc.
        force: str, name of bot to force into playing
        turn_limit: int, number of maximum turns in a single round
        no_timeout: bool, run halite without per-turn timeout
        priority_sigma: bool, whether to prioritize bots by their sigma rating
        keep_logs: bool, keep halite logs
        keep_replays: bool, keep replay files
        record_dir: str, directory to store replays and halite logs
        halite_binary: str, path to halite executable

        :return: Match
        """
        self._apply_default_settings(kwargs)

        if self.players_max > 3:
            num_contestants = random.choice(kwargs['player_dist'])
        else:
            num_contestants = self.players_min
        contestants = self.pick_contestants(num_contestants, force=kwargs['force'], priority_sigma=kwargs['priority_sigma'])

        size_w = kwargs['map_width'] or kwargs['map_height'] or random.choice(kwargs['map_dist'])
        size_h = kwargs['map_height'] or size_w
        seed = kwargs['map_seed'] or random.randint(10000, 2073741824)

        # self.logger.debug("\n------------------- Creating new match... -------------------")
        cont_str = '\n'.join([str(c) for c in contestants])
        # self.logger.debug(f"Contestants:\n{Player.get_columns()}\n{cont_str}")

        return Match(contestants, size_w, size_h, seed, kwargs['turn_limit'], kwargs['keep_replays'],
                        kwargs['keep_logs'], kwargs['no_timeout'], kwargs['record_dir'], kwargs['halite_binary'])

    def run_match(self, match):
        """
        Run a Match object. At end of match, self.match_callback(match) is called.

        :param match: halite.manager.match.Match object
        :return: Match
        """
        try:
            match.run_match()
            self.match_callback(match)
        except Exception as e:
            import traceback
            raise
        return match

    def add_player(self, name, path):
        """
        Add a player to database.
        :param name: str, name of bot to add
        :param path: str, command to run bot
        :return:
        """
        p = self.db.get_player((name,))
        if len(p) == 0:
            self.db.add_player(name, path)
        else:
            raise ValueError("Bot name %s ALREADY USED! No bot added" %(name))

    def delete_player(self, name):
        """
        Remove bot from database.
        :param name: str, bot name to remove
        :return:
        """
        self.db.delete_player(name)

    def edit_path(self, name, path):
        """
        Change path/command of bot.
        :param name: str, bot name to change
        :param path: str, command to run bot
        :return:
        """
        p = self.db.get_player((name,))
        if not p:
            pass
        else:
            p = Player.parse_player_record(p[0])
            self.db.update_player_path(name, path)

    def get_replay_filename(self, id):
        """
        Get filename of stored replay.
        :param id: int, 0:latest, <0:run match backwards from last, >0:match reference number
        :return: (id, filename), (int:match reference number, str or None:replay filename)
        """
        ID, filename = self.db.get_replay_filename(id)
        if filename == 'No Replay Was Stored':
            return ID, filename
        elif os.path.isfile(filename):
            return ID, filename
        else:
            return ID, None

    def view_replay(self, filename):
        """
        View replay by filename
        :param filename: str, replay file
        :return:
        """
        cmd = self.visualizer_cmd.replace('FILENAME', filename)
        subprocess.Popen(cmd, shell=True)

    def _apply_default_settings(self, kw):
        '''
        player_dist: [N,N,N], distribution of player count, e.g. [2,4]
        map_width: int, map units in width
        map_height: int, map units in height
        map_dist: [N,N,N], distribution of map size (overridden if a dimension specified)
                    e.g. [32,40,48,56,64]
        map_seed: int, seed for halite executable to use when generating maps, etc.
        force: str, name of bot to force into playing
        turn_limit: int, number of maximum turns in a single round
        no_timeout: bool, run halite without per-turn timeout
        priority_sigma: bool, whether to prioritize bots by their sigma rating
        keep_logs: bool, keep halite logs
        keep_replays: bool, keep replay files
        record_dir: str, directory to store replays and halite logs
        halite_binary: str, path to halite executable
        '''
        kw.setdefault('priority_sigma', self.priority_sigma)
        kw.setdefault('player_dist', self.player_dist)
        kw.setdefault('map_dist', self.map_dist)
        kw.setdefault('map_width', self.map_width)
        kw.setdefault('map_height', self.map_height)
        kw.setdefault('map_seed', self.map_seed)
        kw.setdefault('force', self.force)
        kw.setdefault('no_timeout', self.no_timeout)
        kw.setdefault('turn_limit', self.turn_limit)
        kw.setdefault('keep_logs', self.keep_logs)
        kw.setdefault('keep_replays', self.keep_replays)
        kw.setdefault('record_dir', self.record_dir)
        kw.setdefault('halite_binary', self.halite_binary)
