# Recuperer des donnees dans un Excel et utiliser ces donnees pour faire des calculs en utilisant xlwings
import xlwings as xw
from market import Market
from option_trade import Option
from tree import TrinomialTree
from outil_convergence import outil_convergence
from arbre_visual import compare_and_display_in_excel
import math
import matplotlib.pyplot as plt
import numpy as np
from blackscholes import bs_price
from node import Node
import time
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Connexion à l’Excel
wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main/TrinomialAndBS_Pricer_V2.xlsm')
sheet = wb.sheets['Paramètres']

# Lire les paramètres du marché
S0 = sheet.range("A2").value  # Prix initial de l’actif sous-jacent
K = sheet.range("E2").value  # Prix d’exercice de l’option
sigma = sheet.range("B3").value  # Volatilité
r = sheet.range("B5").value  # Taux d’intérêt sans risque
t0 = sheet.range("H2").value  # Temps initial
T = sheet.range("E3").value  # Maturité de l’option
N = int(sheet.range("H3").value)  # Nombre de pas dans l’arbre
N_values = [n for n in range(1, N+1)]  # Pour l’outil de convergence


