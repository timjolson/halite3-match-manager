
import os
import copy
import json
import shutil
import skills
import logging
from skills import trueskill
from subprocess import Popen, PIPE, call


def update_skills(players, ranks):
    """ Update player skills based on ranks from a match """
    teams = [skills.Team({player.name: skills.GaussianRating(player.mu, player.sigma)}) for player in players]
    match = skills.Match(teams, ranks)
    calc = trueskill.FactorGraphTrueSkillCalculator()
    game_info = trueskill.TrueSkillGameInfo()
    game_info.dynamics_factor = 0.1
    updated = calc.new_ratings(match, game_info)
    logging.debug("\nUpdating ranks")
    for team in updated:
        player_name, skill_data = next(iter(team.items()))    #in Halite, teams will always be a team of one player
        player = next(player for player in players if player.name == str(player_name))   #this suggests that players should be a dictionary instead of a list
        player.mu = skill_data.mean
        player.sigma = skill_data.stdev
        player.update_skill()
        logging.debug("skill = %4f  mu = %3f  sigma = %3f  name = %s" % (player.skill, player.mu, player.sigma, str(player_name)))

class Match:
    def __init__(self, players, width, height, seed, turn_limit, keep_replays, keep_logs, no_timeout, record_dir, halite_binary):
        self.map_seed = seed
        self.map_height = height
        self.map_width = width
        self.players = players
        self.paths = [player.path for player in players]
        self.finished = False
        self.results = [0 for _ in players]
        self.return_code = None
        self.results_string = ""
        self.replay_file = ""
        self.record_dir = record_dir
        self.halite_binary = halite_binary
        self.turn_limit = turn_limit
        self.total_time_limit = 60*5.0  # 5 minutes
        self.timeouts = []
        self.num_players = len(players)
        self.keep_replay = keep_replays
        self.keep_logs = keep_logs
        self.no_timeout = no_timeout
        self.parameters = None
        self.logs = None
        self.map_generator = None

    def __repr__(self):
        title1 = "Match between " + ", ".join([p.name for p in self.players]) + "\n"
        title2 = "Binaries are " + ", ".join(self.paths) + "\n"
        dims = "dimensions = " + str(self.map_width) + ", " + str(self.map_height) + "\n"
        results = "\t".join([str(i) + " " + j for i, j in zip(self.results, [p.name for p in self.players])]) + "\n"
        replay = self.replay_file + "\n"
        return title1 + title2 + dims + results + replay

    def get_command(self):
        result = [self.halite_binary]
        result.append("--height " + str(self.map_height))
        result.append("--width " + str(self.map_width))
        result.append('' if not self.turn_limit else ("--turn-limit " + str(self.turn_limit)))
        result.append('--no-logs' if not self.keep_logs else '')
        result.append('--no-replay' if not self.keep_replay else '')
        if self.keep_replay or self.keep_logs:
            result.append('--replay-directory ' + str(self.record_dir))
        result.append('--no-timeout' if self.no_timeout else '')
        result.append("--results-as-json")
        result.append("-s " + str(self.map_seed))

        return [r for r in result if r] + self.paths

    def run_match(self):
        command = self.get_command()
        logging.debug("Command = " + str(command))
        p = Popen(command, stdin=None, stdout=PIPE, stderr=None)
        results, _ = p.communicate(None, self.total_time_limit)
        self.results_string = results.decode('ascii')
        self.return_code = p.returncode
        self.parse_results_string()
        update_skills(self.players, copy.deepcopy(self.results))

    def parse_results_string(self):
        logging.debug("parsing results a")
        data = json.loads(self.results_string)
        logging.debug("parsing results b")
        self.logs = data['error_logs']
        logging.debug("parsing results c")
        self.map_height = data['map_height']
        logging.debug("parsing results d")
        self.map_width = data['map_width']
        logging.debug("parsing results e")
        self.map_seed = data['map_seed']
        logging.debug("parsing results f")
        self.map_generator = data['map_generator']
        logging.debug("parsing results g")
        self.replay_file = data.get('replay', 'No Replay Was Stored')
        logging.debug("parsing results h")
        self.stats = data['stats']
        logging.debug("parsing results i")
        self.terminated = data['terminated']
        logging.debug("parsing results j")
        for player_index_string in self.stats:
            player_index = int(player_index_string)
            rank_string = self.stats[player_index_string]['rank']
            halite_string = self.stats[player_index_string]['score']
            self.results[player_index] = str((rank_string, halite_string))
