"""
We should eventually convert to using the ESPN API

Matchup Box Scores: https://fantasy.espn.com/apis/v3/games/fba/seasons/2020/segments/0/leagues/368749?view=mBoxscore
Player Stats: https://fantasy.espn.com/apis/v3/games/fba/seasons/2020/segments/0/leagues/368749?view=mRoster
Weekly Matchups: https://site.api.espn.com/apis/fantasy/v2/games/fba/games?useMap=true&dates=20191219&pbpOnly=true

"""

import requests, json, time
from lxml import html
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd

""" REVERSE ENGINEERED ESPN API STATS """

id_to_stattype = {
    '012020' : '7-day',
    '022020' : '15-day',
    '102019' : 'last-proj',
    '002020' : 'this-season',
    '102020' : 'this-proj',
    '032020' : '30-day',
    '002019' : 'last-season',
}

stattype_to_id = {v: k for k, v in id_to_stattype.items()}

idx_to_statname = {
    '0' : 'PTS',
    '1' : 'BLK',
    '2' : 'STL',
    '3' : 'AST',
    '6' : 'REB',
    '11': 'TO',
    '13': 'FGM',
    '14': 'FGA',
    '15': 'FTM',
    '16': 'FTA',
    '17': '3PM',
    '18': '3PA',
    '19': 'FG%',
    '20': 'FT%',
    '40': 'MIN',
}

statname_to_idx = {v: k for k, v in idx_to_statname.items()}

class Player(object):
    def __init__(self, p_id, info):
        self._id = p_id
        self.info = info
        self.custompred = {}

    def _stats(self, stattype, statnames):
        # statnames is a list of [statname]
        required_id = stattype_to_id[stattype]

        for stat_obj in self.info["stats"]:
            if stat_obj["id"] == required_id and 'averageStats' in stat_obj:
                avg_stats = stat_obj['averageStats']
                total_stats = stat_obj['stats']
                num_games = int(total_stats['0'] / avg_stats['0'])

                return np.array([avg_stats[statname_to_idx[statname]] for statname in statnames]), num_games

        return np.zeros(len(statnames)), np.nan # data not found

    def _insert_custom_pred(self, custompred):
        self.custompred = custompred

    def _pred_stats(self, statnames, pred_method=None):
        # TODO: pred method not implemented

        last_30, gp = self._stats('30-day', statnames)
        final_pred = last_30

        if self.custompred: # overwrite preds with custom pred
            for idx, statname in enumerate(statnames):
                if statname in self.custompred.keys():
                    final_pred[idx] = self.custompred[statname]

        return final_pred

    def _ownership_pct(self):
        return self.info["ownership"]["percentOwned"]

    def _name(self):
        return self.info["fullName"]

    def _pro_team(self):
        return self.info["proTeamId"]

""" SCRAPING FUNCTIONS """

def get_json(url):
    return json.loads(requests.get(url).text)

def get_daily_games(dates):
    start_time = time.time()

    results = {} # dict of date ('YYYYMMDD') -> list of team_ids playing

    for date in dates:
        results[date] = []
        matchup_url = f"https://site.api.espn.com/apis/fantasy/v2/games/fba/games?useMap=true&dates={date}&pbpOnly=true"
        matchup_json = get_json(matchup_url)

        for el in matchup_json['events']:
            results[date].append(el['competitors'][0]['id'])
            results[date].append(el['competitors'][1]['id'])

    end_time = time.time()
    print("Pro Schedule loaded. Time taken: {:f}s".format(end_time - start_time))
    return results

def get_teams(league_id):
    teams = {}

    team_url = f'https://fantasy.espn.com/apis/v3/games/fba/seasons/2020/segments/0/leagues/{league_id}'
    team_json = get_json(team_url)

    for team in team_json['teams']:
        team_id = team["id"]
        team_name = team["abbrev"]
        teams[team_id] = team_name

    return teams

def get_rostered_players(league_id, team_ids):
    start_time = time.time()

    player_stats = {} # dict of player_id -> player object that stores stats
    team_rosters = {} # dict of team_id -> list of player_id
    for team_id in team_ids:
        team_rosters[team_id] = []

    player_url = f'https://fantasy.espn.com/apis/v3/games/fba/seasons/2020/segments/0/leagues/{league_id}?view=kona_player_info'
    player_json = get_json(player_url)

    for player_info in player_json['players']:
        player_id = player_info['id']
        team_id = player_info['onTeamId']

        if team_id in team_ids: # a rostered player we need to track
            player_obj = Player(player_id, player_info['player'])
            player_stats[player_id] = player_obj
            team_rosters[team_id].append(player_id)

    end_time = time.time()
    print("Player Stats loaded. Time taken: {:f}s".format(end_time - start_time))
    return player_stats, team_rosters

def get_matchups(league_id):
    matchup_url = 'https://fantasy.espn.com/apis/v3/games/fba/seasons/2020/segments/0/leagues/368749?view=mBoxscore'
    matchup_json = get_json(matchup_url)

    for matchup in matchup_json['schedule']:
        pass
