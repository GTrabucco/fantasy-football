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

END_YEAR = 2018
TEAM_NUM = 10
LEAGUE = 'nhs'
NHS_TEAM_NAMES = ['Evan Turner','Ryan Wentworth','Jack Gowetski','Alex Caulfield','Brendan Chin','Aiden O\'Connor','Giulian Trabucco','auggie coll','Dante Coppola','Ben Newman']
teams = []

class Team():
	def __init__(self, name):
		self.name = name
		self.week_score = 0.0
		self.wins = 0
		self.losses = 0
		self.ties = 0
		self.highest = 0
		self.lowest = 200
		self.luck = 0.0
		self.top_score = 0
		self.low_score = 0
		self.actual_wins = 0.0
		self.avg_pf = 0
		self.exp_wins = 0
		self.std = 0

def initialize_teams():
	if (LEAGUE == 'nhs'):	
		for team in NHS_TEAM_NAMES:
			t = Team(team)
			teams.append(t)
	else:
		print('error')

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
			h_name = m('.team-owner-col').eq(1).text()
			if(year == 2012):
				if (a_name == ""):
					a_name = 'Ryan Wentworth'
				elif(h_name == ""):
					h_name = 'Ryan Wentworth'

			if(year <= 2015):
				if a_name == 'Kyle Bourke':
					a_name = 'Brendan Chin'
				elif h_name == 'Kyle Bourke':
					h_name = 'Brendan Chin'

			a_record = m('.team-record').eq(0).text()[1:m('.team-record').eq(0).text().index("-")]
			h_record = m('.team-record').eq(1).text()[1:m('.team-record').eq(1).text().index("-")]

			a_team = [x for x in teams if x.name == a_name][0]
			h_team = [x for x in teams if x.name == h_name][0]
			if(week == 0):
				a_team.actual_wins = a_team.actual_wins + float(a_record)
				h_team.actual_wins = h_team.actual_wins + float(h_record)
			a_team.week_score = float(m('.link').eq(0).text())
			h_team.week_score = float(m('.link').eq(1).text())
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

					if(count == 0):
						j.low_score = j.low_score + 1

					prev = i
					count = count - 1
					break
		week = week + 1

def calculate_luck():
	for i in teams:
		exp_win_pct = float(i.wins/(i.wins + i.losses))
		num_weeks = 91
		i.luck = i.luck + (i.actual_wins - ((exp_win_pct) * num_weeks))

def graph_stats():
	style.use('ggplot')
	scores = {"Team": [i.name for i in teams],
		  "Wins": [i.wins for i in teams],
		  "Loses": [i.losses for i in teams],
		  "Highest": [i.highest for i in teams],
		  "Lowest": [i.lowest for i in teams],
		  "Top Scorer": [i.top_score for i in teams],
		  "Lowest Scorer": [i.low_score for i in teams],
		  "Luck": [i.luck for i in teams],
		  "Actual Wins": [i.actual_wins for i in teams],
		  }

	df = pd.DataFrame(scores)
	df.set_index('Team', inplace=True)
	df.sort_values(by=['Wins'], ascending=False, inplace=True)
	print(df)

def main():
	initialize_teams()
	year = 2012
	weeks = 13
	while year <= 2018:
		schedule = f'../data/{LEAGUE}/{year}/schedule{year}.htm'
		if (year == 2019):
			weeks = 1
		evaluate_matchups(schedule, weeks, year)
		calculate_luck()
		year = year + 1
	graph_stats()

main()