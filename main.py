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
wb = xw.Book('/Users/lanphuongvu/Downloads/TrinomialAndBS_Pricer_V2-2.xlsm')
sheet = wb.sheets['Paramètres']

# Lire les paramètres du marché
S0 = sheet.range('B3').value          # Prix initial du sous-jacent
r = sheet.range('B5').value           # Taux d’intérêt sans risque
sigma = sheet.range('B3').value       # Volatilité
exdivdate = sheet.range('B7').value  # Date de détachement du dividende

t0 = sheet.range('H2').value       # Date actuelle
T = sheet.range('B9').value        # Maturité de l’option
K = sheet.range('E2').value       # Prix d’exercice de l’option

