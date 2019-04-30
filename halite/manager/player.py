class Player:
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
        #return "{:<20}{:<20}{:^6}{:10.4f}{:10.4f}{:10.4f}   {:>5} {:>5}        {:<30}".format(self.name, str(self.last_seen), self.rank, self.skill, self.mu, self.sigma, self.ngames, self.active, self.path)
        return "{:<20}{:<20}{:^6}{:10.4f}{:10.4f}{:10.4f}   {:>5} {:>5}".format(self.name, str(self.last_seen), self.rank, self.skill, self.mu, self.sigma, self.ngames, self.active)

    def update_skill(self):
        self.skill = self.mu - (self.sigma * 3)
        self.ngames += 1

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def get_columns():
        return "{:<20}{:<20}{:^6}  {:^10}{:^10}{:^10}{:^8}{:^8}".format("name", "last_seen", "rank", "skill", "mu",
                                                                     "sigma", "ngames", "active")

    @staticmethod
    def parse_player_record(player):
        (player_id, name, path, last_seen, rank, skill, mu, sigma, ngames, active) = player
        return Player(name, path, last_seen, rank, skill, mu, sigma, ngames, active)
