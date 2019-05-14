import copy
import json
import skills
import logging
from skills import trueskill
from subprocess import Popen, PIPE


class Match:
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())

    def __init__(self, players, width, height, seed, turn_limit, keep_replays, keep_logs, no_timeout, record_dir, halite_binary):
        self.map_seed = seed
        self.map_height = height
        self.map_width = width
        self.players = players
        self.paths = [player.path for player in players]
        self.finished = False
        self.stats = None
        self.terminated = False
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

        cmd = [r for r in result if r] + self.paths
        self.logger.debug("Command = " + str(' '.join(cmd)))
        return cmd

    def run_match(self):
        command = self.get_command()
        p = Popen(command, stdin=None, stdout=PIPE, stderr=None)
        self.logger.debug(f"Command executing for < {self.total_time_limit} seconds...")
        results, _ = p.communicate(None, self.total_time_limit)
        self.finished = True
        self.results_string = results.decode('ascii')
        self.return_code = p.returncode
        self.logger.debug(f"Command returned: {self.return_code}")
        self.parse_results_string()
        self.update_skills(self.players, copy.deepcopy(self.results))

    def parse_results_string(self):
        data = json.loads(self.results_string)
        self.logs = data['error_logs']
        self.map_height = data['map_height']
        self.map_width = data['map_width']
        self.map_seed = data['map_seed']
        self.map_generator = data['map_generator']
        self.replay_file = data.get('replay', 'No Replay Was Stored')
        self.stats = data['stats']
        self.terminated = data['terminated']
        for player_index_string in self.stats:
            player_index = int(player_index_string)
            rank_string = self.stats[player_index_string]['rank']
            halite_string = self.stats[player_index_string]['score']
            self.results[player_index] = str((rank_string, halite_string))

    def update_skills(self, players, ranks):
        """ Update player skills based on ranks from a match """
        teams = [skills.Team({player.name: skills.GaussianRating(player.mu, player.sigma)}) for player in players]
        match = skills.Match(teams, ranks)
        calc = trueskill.FactorGraphTrueSkillCalculator()
        game_info = trueskill.TrueSkillGameInfo()
        game_info.dynamics_factor = 0.2
        updated = calc.new_ratings(match, game_info)
        self.logger.debug("\nUpdating ranks")
        for team in updated:
            player_name, skill_data = next(iter(team.items()))  # in Halite, teams will always be a team of one player
            player = next(player for player in players if player.name == str(
                player_name))  # this suggests that players should be a dictionary instead of a list
            player.mu = skill_data.mean
            player.sigma = skill_data.stdev
            player.update_skill()
            self.logger.debug("skill = %4f  mu = %3f  sigma = %3f  name = %s" % (player.skill, player.mu, player.sigma, str(player_name)))
