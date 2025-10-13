# Recuperer des donnees dans un Excel et utiliser ces donnees pour faire des calculs en utilisant xlwings
import xlwings as xw
from market import Market
from option_trade import Option
from tree import TrinomialTree
from outil_convergence import outil_convergence
import math
import matplotlib.pyplot as plt
import numpy as np
from blackscholes import bs_price
from node import Node
import time
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
# Connexion à l’Excel
wb = xw.Book('Option-Pricing.xlsx')
sheet = wb.sheets['Main']

# Lire les paramètres du marché

