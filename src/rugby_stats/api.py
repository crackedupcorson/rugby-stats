from flask import Flask, request
from batch import BatchProcessor
import logging
import squad as squad
from waitress import serve
from werkzeug.middleware.dispatcher import DispatcherMiddleware


app = Flask(__name__)
#app.wsgi_app = DispatcherMiddleware(app.wsgi_app)
season = 202501
backoff_seconds = 10
logger = logging.getLogger(__name__)
processor = BatchProcessor(season=season, backoff_seconds=backoff_seconds)

@app.route('/player/stats')
def get_player_stats(): 
    player_id = int(request.args.get('player_id'))
    return processor.process_player(player_id)


@app.route('/team/player-stats')
def get_player_stats_for_team():
    team_id = request.args.get('team_id')
    """Fetch and process stats for all players in a team."""
    squad_data = squad.fetch_squad(team_id)
    player_ids = squad.extract_player_ids(squad_data)
    response = processor.process_batch(player_ids)
    logging.info(f"Processed stats for team {team_id} with {len(player_ids)} players")
    return response, 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)