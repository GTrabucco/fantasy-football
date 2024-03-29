from espnff import League
from textblob import TextBlob
from glob import glob
import pandas as pd
from matplotlib import style
import matplotlib.pyplot as plt
import time
import requests
from pyquery import PyQuery as pq 
import re
import urllib.request
import operator
import statistics
import numpy as np
from pyquery import PyQuery as pq
from IPython.display import display, HTML

END_YEAR = 2019
TEAM_NUM = 12
LEAGUE = 'dm'
teams = []
CURRENT_WEEKS = 7

class Team():
	def __init__(self, name):
		self.name = name
		self.week_score = 0.0
		self.week_opp = None
		self.pf = 0.0
		self.pa = 0.0
		self.wins = 0
		self.losses = 0
		self.ties = 0
		self.highest = 0
		self.lowest = 200
		self.luck = 0.0
		self.top_score = 0
		self.low_score = 0
		self.actual_wins = 0.0
		self.exp_wins = 0
		self.std = 0
		self.shelled = 0
		self.tuna = 0
		self.prev_rank = 0
		self.rank = 0
		self.position = 0

def evaluate_matchups(schedule, weeks, year):
	with open(schedule) as f:
		html = f.read()
	doc = pq(html)
	matchups = doc('table.Table2__table-scroller.Table2__table')
	week = 0
	while week < weeks:
		matchup = matchups.eq(week)('tbody')
		#get weekly scores
		for m in matchup('tr').items():
			a_name = m('.team-owner-col').eq(0).text()
			if (a_name == ""):
				a_name = 'Ryan Wentworth'
			elif a_name == 'Kyle Bourke':
				a_name = 'Brendan Chin'

			if any(t.name == a_name for t in teams) == False:
				teams.append(Team(a_name))

			h_name = m('.team-owner-col').eq(1).text()
			if(h_name == ""):
				h_name = 'Ryan Wentworth'
			elif h_name == 'Kyle Bourke':
				h_name = 'Brendan Chin'

			if any(t.name == h_name for t in teams) == False:
				teams.append(Team(h_name))

			a_record = m('.team-record').eq(0).text()[1:m('.team-record').eq(0).text().index("-")]
			h_record = m('.team-record').eq(1).text()[1:m('.team-record').eq(1).text().index("-")]

			a_team = [x for x in teams if x.name == a_name][0]
			h_team = [x for x in teams if x.name == h_name][0]
			a_team.week_opp = h_team
			h_team.week_opp = a_team

			if(week == CURRENT_WEEKS-1):
				a_team.actual_wins = a_team.actual_wins + float(a_record)
				h_team.actual_wins = h_team.actual_wins + float(h_record)
			a_team.week_score = float(m('.link').eq(0).text())
			h_team.week_score = float(m('.link').eq(1).text())
			a_team.pf = a_team.pf + a_team.week_score
			a_team.pa = a_team.pa + h_team.week_score
			h_team.pf = h_team.pf + h_team.week_score
			h_team.pa = h_team.pa + a_team.week_score

		sorted_scores = sorted(teams, key=lambda x: x.week_score, reverse=True)
		
		count = TEAM_NUM-1
		prev = 0
		double = False
		added = 0
		lost = 0

		for i in sorted_scores:	
			for j in teams:
				if i.name == j.name:

					score = i.week_score

					if prev != 0 and score == prev.week_score:
						j.wins = j.wins + added
						j.losses =  j.losses + lost
						double = True
					else:
						j.wins =  j.wins + count
						j.losses = j.losses + ((TEAM_NUM-1) - count)
						added = count
						lost = (TEAM_NUM-1) - count

					if(score > j.highest):
						j.highest = score

					if(score < j.lowest):
						j.lowest = score

					if(count == (TEAM_NUM-1)):
						j.top_score = j.top_score + 1
						j.week_opp.shelled = j.week_opp.shelled + 1

					if(count == 0):
						j.low_score = j.low_score + 1
						j.week_opp.tuna = j.week_opp.tuna + 1

					prev = i
					count = count - 1
					break
		if CURRENT_WEEKS != 13 and week == (CURRENT_WEEKS-2):
			graph = graph_stats()
			place = 1
			for index, row in graph.iterrows():
				team = [x for x in teams if x.name == index][0]
				team.prev_rank = place
				place = place + 1

		week = week + 1

	graph = graph_stats()
	place = 1
	for index, row in graph.iterrows():
		team = [x for x in teams if x.name == index][0]
		team.rank = place
		place = place + 1

	for team in teams:
		difference = team.prev_rank - team.rank
		if difference < 0:
			team.position = "-" + str(abs(difference))
		elif difference == 0:
			team.position = "--"
		else:
			team.position = "+" + str(abs(difference))

def calculate_luck():
	for i in teams:
		exp_win_pct = float(i.wins/(i.wins + i.losses))
		i.luck = i.luck + (i.actual_wins - ((exp_win_pct) * CURRENT_WEEKS))

def color_values(val):
	color = 'white'
	if val[0] == "+":
		color = 'green'
	elif val[0] == "-":
		color = 'green'
	else:
		color = 'red'
	return 'color: %s' % color

def graph_stats():
	style.use('ggplot')
	scores = {
	      "Change": [i.position for i in teams],
		  "Team": [i.name for i in teams],
		  "Wins": [i.wins for i in teams],
		  "Loses": [i.losses for i in teams],
		  "Highest": [i.highest for i in teams],
		  "Lowest": [i.lowest for i in teams],
		  "Top Scorer": [i.top_score for i in teams],
		  "Lowest Scorer": [i.low_score for i in teams],
		  "Luck": [i.luck for i in teams],
		  "Actual Wins": [i.actual_wins for i in teams],
		  "Points For": [i.pf for i in teams],
		  "Points Against": [i.pa for i in teams],
		  "Shelled": [i.shelled for i in teams],
		  "Lowest Faced": [i.tuna for i in teams]
		  }

	df = pd.DataFrame(scores)
	df.set_index('Team', inplace=True)
	df.sort_values(by=['Wins', "Points For"], ascending=False, inplace=True)
	return df	

def print_stats(df):
	df.style.applymap(color_values, subset=['Change']).render() #doesnt work in terminal
	print(df)

def main():
	year = 2019
	weeks = 13
	while year <= END_YEAR:
		schedule = f'../data/{LEAGUE}/{year}/schedule{year}.htm'
		if (year == 2019):
			weeks = CURRENT_WEEKS
		evaluate_matchups(schedule, weeks, year)
		calculate_luck()
		year = year + 1
	graph = graph_stats()
	print_stats(graph)

main()