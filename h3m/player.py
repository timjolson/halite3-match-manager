class Player:
    """
    Store a player and its stats.
    """
    def __init__(self, name, path, last_seen = "", rank = 1000, skill = 0.0, mu = 25.0, sigma = (25.0 / 3.0), ngames = 0, active = 1):
        self.name = name
        self.path = path
        self.last_seen = last_seen
        self.rank = rank
        self.skill = skill
        self.mu = mu
        self.sigma = sigma
        self.ngames = ngames
        self.active = active

    def __repr__(self):
        return self._column_format().format(self.name, str(self.last_seen), self.rank, self.skill, self.mu, self.sigma, self.ngames, self.active)

    def update_skill(self):
        self.skill = self.mu - (self.sigma * 3)
        self.ngames += 1

    def __eq__(self, other):
        return self.name == other.name

    @classmethod
    def get_columns(cls):
        return cls._header_format().format("name", "last_seen", "rank", "skill", "mu",
                                                                     "sigma", "ngames", "active")

    @staticmethod
    def _column_format():
        return "{:<11}{:<20}{:^6}{:8.3f}{:8.3f}{:8.3f}{:>6}{:>8}"

    @staticmethod
    def _header_format():
        return "{:<11}{:<20}{:^7}{:^10}{:^5}{:^10} {:^7}{:^8}"

    @staticmethod
    def parse_player_record(player):
        (player_id, name, path, last_seen, rank, skill, mu, sigma, ngames, active) = player
        return Player(name, path, last_seen, rank, skill, mu, sigma, ngames, active)
