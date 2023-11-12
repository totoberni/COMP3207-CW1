import json

class Player:
    def __init__(self, id, username, password, games_played, total_score):
        # TODO: Maybe there should be test here maybe they mess with the player_register function
        #if len(name) < 3:
        #    raise ValueError("name must be at least 3 characters")
        self.id = id
        self.username = username
        self.password = password
        self.games_played = games_played
        self.total_score = total_score

    def to_dict(self):
        return {"id": self.id, 
                "username": self.username, 
                "password": self.password, 
                "games_played": self.games_played, 
                "total_score": self.total_score}    

    def to_json(self):
        return json.dumps(self.to_dict(self))    