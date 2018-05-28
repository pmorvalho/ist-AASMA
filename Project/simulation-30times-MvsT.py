import networkx as nx
import matplotlib.pylab as plt
import matplotlib.animation as animation
import copy
from random import *
import numpy as np
import graph_utils
from company import *
from truck import *
from client import *

class Simulation(object):
	def __init__(self, 
		n_nodes, graph_type, graph_param, graph_min_weight, graph_max_weight,
		n_companies, n_trucks, 
		truck_threshold, company_init_money, uni_cost, profit_margin, tax,
		risk, min_offer_val, max_offer_val,
		existence_tax, p_edge_explosion, p_truck_explosion):

		# network params
		self.n_nodes = n_nodes
		self.graph_type = graph_type
		self.graph_param = graph_param
		self.graph_min_weight = graph_min_weight
		self.graph_max_weight = graph_max_weight
		
		# agents params
		self.n_companies = n_companies
		self.n_trucks = n_trucks

		# company params
		self.truck_threshold = truck_threshold
		self.company_init_money = company_init_money
		self.uni_cost = uni_cost
		self.profit_margin = profit_margin
		self.tax = tax

		# client params
		self.risk = risk
		# self.utilities = utilities
		self.min_offer_val = min_offer_val
		self.max_offer_val = max_offer_val

		# events params
		self.existence_tax = existence_tax
		self.p_edge_explosion = p_edge_explosion
		self.p_truck_explosion = p_truck_explosion		

		self.completedOffers = 0

	def build_graph(self):
		if self.graph_type == "random":
			return graph_utils.generate_weighted_random_graph(
				n=self.n_nodes, 
				p=self.graph_param,
				min_weight=self.graph_min_weight, 
				max_weight=self.graph_max_weight)
		elif self.graph_type == "scale-free":
			return graph_utils.generate_weighted_barabasi_graph(
				n=self.n_nodes, 
				p=self.graph_param,
				min_weight=self.graph_min_weight, 
				max_weight=self.graph_max_weight)

	def generate_companies(self, graph):
		company_names = ["A", "B", "C", "D","E","F","G","H","I","J","K"]
		companies = sample(list(graph.nodes()), k=self.n_companies)
		companies = [(x, Company(x, self.company_init_money, 
						company_names[i], graph,
						uni_cost=self.uni_cost,
						truck_threshold=self.truck_threshold,
						profit_margin=self.profit_margin,
						tax=self.tax)) for i,x in enumerate(companies)]
		print(companies)
		print("companies printed")
		graph_utils.colormap = []
		graph_utils.set_company_nodes(graph, companies)
		print("setting nodes")
		return companies

	# def resetCompanies(self, companies):
		

	def generate_trucks(self, graph, companies):
		for c in companies:
			c[1].setTrucks([Truck(i, c[1], graph) for i in range(self.n_trucks)])

	def calculateUtilities(self):
		pref = np.array([(randint(1,99)/100) for _ in range(self.n_companies)])
		return list(pref/sum(pref))
		# return [1 for _ in range(self.n_companies)]

	def generate_clients(self, graph, companies):
		i=0
		return [Client(n, 
					[c[1] for c in companies],
					risk=self.risk,
					utilities=self.calculateUtilities(),
					min_offer_val=self.min_offer_val, 
					max_offer_val=self.max_offer_val) for n in graph.nodes if "company" not in graph.node[n]]

	def do_edge_explosion(self, t,graph):
		try:
			e = choice(list(graph.edges()))
		except Exception as e:
			print(f"\tall edges removed t= {t}\t")
			exit()
		graph.remove_edge(e[0],e[1])
		print(f"\tedge removed:\t {e[0]} -- {e[1]} (t={t})")

	def do_game_over(self, companies, company, graph,t):
		print(f"GAME OVER FOR {company[1]} at t={t} -- offers={company[1].completedOffers}")
		companies.remove(company)
		# del graph.node[company[0]]['company']
		# graph_utils.colormap[company[0]]= "#%06x" % 0xDDDDDD
		return company[1]

	def drawPlot(self, x_data, title, xlabel, ylabel, legend):
		plt.figure(1)
		plt.title(title)
		plt.xlabel(xlabel)
		plt.ylabel(ylabel)
		# colors = ["red", "black", "blue", "orange", "green"]
		for i in range(len(x_data)):
			plt.plot(list(range(len(x_data[i]))), x_data[i], label="Company "+legend[i][1], color=legend[i][0])
		plt.legend()
		plt.show()

	def run(self, g, companies, clients, iterations):
		print(companies)
		money_per_company = []
		dict_companies = dict([])
		for i in range(len(companies)):
			money_per_company.append([])
			dict_companies[companies[i][1]] = i

		for _ in range(iterations):
			for m in money_per_company:
				m.append(0)

		for i in range(iterations):
			# for j in range(len(money_per_company)):
			# 	money_per_company[j].append(0)
			if len(companies) == 0:
				print("NO MORE COMPANIES")
				return money_per_company
			if len(companies) == 1:
				print(f"WINNER: {companies[0][1]} -- t={i} -- offers={companies[0][1].completedOffers}")
				return money_per_company

			if (randint(1,99)/100) < self.p_edge_explosion:
				self.do_edge_explosion(i, g)

			for cli in clients:
				cli.go(i)

			for c in companies:
				if c[1].money <= 0:
					self.completedOffers += c[1].getCompletedOffers()
					company_gameover = self.do_game_over(companies, c, g, i)
					for cli in clients:
						cli.removeCompany(company_gameover)
					continue

				c[1].money -= self.company_init_money*self.existence_tax # impostos por existencia
				c[1].go(g, i)
				money_per_company[dict_companies[c[1]]][i] = c[1].money

		for c in companies:
			print(f"SURVIVOR: {c} -- t={i} -- offers={c[1].completedOffers}")
			self.completedOffers += c[1].getCompletedOffers()

		# print(f"OFFERS COMPLETED: {self.completedOffers}")
		return money_per_company
		# self.drawPlot(money_per_company, "Money vs Time", "Time", "Money")

def main():

	s = Simulation(
		n_nodes=20, graph_type="random", graph_param=0.2, 
		graph_min_weight=1, graph_max_weight=10,
		n_companies=5, n_trucks=7, truck_threshold=100, company_init_money=2500,
		uni_cost=1, profit_margin=1.5, tax=0.05,
		risk=(randint(1,99)/100),
		min_offer_val=20, max_offer_val=80,
		existence_tax=0.05, p_edge_explosion=0.000, p_truck_explosion=0.01)
	
	g = s.build_graph()
	companies = s.generate_companies(g)
	s.generate_trucks(g, companies)
	graph_utils.draw_graph(g)
	graph_utils.show_graphs()
	cpy_companies = [(c[0], copy.deepcopy(c[1])) for c in companies]
	clients = s.generate_clients(g, cpy_companies)
	money_per_company = []
	iterations = 100
	tests = 30
	for _ in range(s.n_companies):
		money_per_company.append([])
	
	for _ in range(iterations):
		for m in money_per_company:
			m.append(0)

	for _ in range(tests):
		mc = s.run(g, list(cpy_companies), list(clients), iterations)
		for i in range(len(mc)):
			money_per_company[i] = list(np.array(money_per_company[i]) + np.array(mc[i]))
		cpy_companies = [(c[0], copy.deepcopy(c[1])) for c in companies]
		for cli in clients:
			cli.setCompanies([c[1] for c in cpy_companies])

	for mc in money_per_company:
		mc = np.array(mc)/10
	legend = [(graph_utils.colormap[c[0]], c[1].name) for c in companies]
	s.drawPlot(money_per_company, "Money vs Time", "Time", "Money", legend)

if __name__ == '__main__':
	main()
	
