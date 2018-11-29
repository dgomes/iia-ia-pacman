from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'grades.sqlite')
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    player = db.Column(db.String(25))
    map = db.Column(db.String(25))
    n_ghosts = db.Column(db.Integer)
    l_ghosts = db.Column(db.Integer)
    score = db.Column(db.Integer)

    def __init__(self, player, map, n_ghosts, l_ghosts, score):
        self.player = player
        self.map = map
        self.n_ghosts = n_ghosts
        self.l_ghosts = l_ghosts
        self.score = score

class GameSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'timestamp', 'player', 'map', 'n_ghosts', 'l_ghosts', 'score')


game_schema = GameSchema()
games_schema = GameSchema(many=True)


# endpoint to create new game
@app.route("/game", methods=["POST"])
def add_game():
    player = request.json['player']
    map = request.json['map']
    n_ghosts = request.json['n_ghosts']
    l_ghosts = request.json['l_ghosts']
    score = request.json['score']

    new_game = Game(player, map, n_ghosts, l_ghosts, score)

    db.session.add(new_game)
    db.session.commit()

    return game_schema.jsonify(new_game) 


# endpoint to show all games 
@app.route("/game", methods=["GET"])
def get_game():
    all_games = Game.query.all()
    result = games_schema.dump(all_games)
    return jsonify(result.data)


# endpoint to get game detail by id
@app.route("/game/<id>", methods=["GET"])
def game_detail(id):
    game = Game.query.get(id)
    return game_schema.jsonify(game)


if __name__ == '__main__':
    app.run(debug=True)
