# Recuperer des donnees dans un Excel et utiliser ces donnees pour faire des calculs en utilisant xlwings
import xlwings as xw
from models.market import Market
from models.option_trade import Option
from models.tree import TrinomialTree
import math
import numpy as np
from utils.utils_bs import bs_price
from models.node import Node
import time
import datetime as dt
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

from dataclasses import dataclass
from typing import Optional, Literal

# Connexion à l’Excel
wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main/TrinomialAndBS_Pricer_V2.xlsm')
sheet = wb.sheets['Paramètres']

# Lire les paramètres du marché@dataclass
@dataclass
class Inputs:
    # Marché
    spot: float
    vol: float
    rate: float
    div: float
    div_ex_date: dt.datetime

    # Option
    strike: float
    maturity: dt.datetime
    cp: Literal["Call", "Put"]
    exercise: Literal["EU", "US"]

    # Arbre
    pricing_date: dt.datetime
    n_steps: int
    dt_step: float
    alpha: float

    # Affichages/optim 
    tree_stock: bool
    tree_reach: bool
    tree_option: bool
    pruning: bool
    prune_thresh: float

    # Sélection
    method: Literal["rec", "back"]
    lang: Literal["py", "vb"]


NR = {
    # Market
    "Spot": "Spot",
    "Vol": "Volatilité",
    "Rate": "Taux",
    "Div": "Dividende",
    "DivDate": "ExDivDate_Dividende",

    # Option
    "Strike": "Strike",
    "Mat": "Maturité",
    "CP": "Call_Put",
    "Ex": "Exercice",

    # Tree / divers
    "PricingDate": "date_pricing",
    "N": "N",
    "DeltaT": "Delta_t",
    "Alpha": "Alpha",
    "ShowStock": "AffichageStock",
    "ShowReach": "AffichageReach",
    "ShowOption": "AffichageOption",
    "Pruning": "Pruning",
    "Thresh": "Seuil",

    # Méthode & Langage
    "Method": "Methode_Pricing",   # B8
    "Lang": "Langage",             # C8

    # Sorties
    "PriceTree": "Prix_Tree",
    "TimeTree": "Time_Tree",
    "PriceBS": "Prix_BS",
    "TimeBS": "Time_BS",
}

def read_inputs(sht: xw.Sheet) -> Inputs:
    n = sht.book.names
    v = lambda key: n[NR[key]].refers_to_range.value

    return Inputs(
        # Marché
        spot=float(v("Spot")),
        vol=float(v("Vol")),
        rate=float(v("Rate")),
        div=float(v("Div")),
        div_ex_date=_to_datetime(v("DivDate")),

        # Option
        strike=float(v("Strike")),
        maturity=_to_datetime(v("Mat")),
        cp=_norm_cp(v("CP")),
        exercise=_norm_ex(v("Ex")),

        # Arbre
        pricing_date=_to_datetime(v("PricingDate")),
        n_steps=int(v("N")),
        dt_step=float(v("DeltaT")),
        alpha=float(v("Alpha")),

        # Flags
        show_tree=_as_bool(v("Show")),
        pruning=_as_bool(v("Pruning")),
        prune_thresh=float(v("Thresh")),

        # Sélection
        method=_norm_method(v("Method")),
        lang=_norm_lang(v("Lang")),
    )


def write_outputs(sht: xw.Sheet, price_tree: float, time_tree: float,
                  price_bs: Optional[float], time_bs: Optional[float]) -> None:
    n = sht.book.names
    n[NR["PriceTree"]].refers_to_range.value = float(price_tree)
    n[NR["TimeTree"]].refers_to_range.value = f"{time_tree:.4f} s"
    if price_bs is not None:
        n[NR["PriceBS"]].refers_to_range.value = float(price_bs)
    if time_bs is not None:
        n[NR["TimeBS"]].refers_to_range.value = f"{time_bs:.4f} s"

def build_market(inp: Inputs) -> Market:
    """Market(S0, r, sigma, T, dividends=None, ...)"""
    # Sécurise T et N (évite T<=0 avec maturité = date_pricing)
    days = (inp.maturity - inp.pricing_date).days
    T_years = max(days, 0) / 365.0
    return Market(S0=inp.spot, r=inp.rate, sigma=inp.vol, T=T_years, dividends=None)

def build_option(inp: Inputs) -> Option:
    """Option(K, is_call=True|False)"""
    return Option(K=inp.strike, is_call=(inp.cp == "Call"))

def build_tree(inp: Inputs, mkt: Market, opt: Option) -> TrinomialTree:
    """TrinomialTree(market, option, N, exercise="european"/"american")"""
    exercise = "european" if inp.exercise == "EU" else "american"

    # Sécurise N >= 1
    N = max(int(inp.n_steps), 1)

    tree = TrinomialTree(market=mkt, option=opt, N=N, exercise=exercise)

    # Certaines versions exigent une étape de construction explicite
    for method in ("build_tree", "build", "construct_tree", "construct", "init_tree", "initialize"):
        if hasattr(tree, method):
            try:
                getattr(tree, method)()              # sans args
            except TypeError:
                try:
                    getattr(tree, method)(mkt, opt)  # avec args
                except TypeError:
                    pass
            break

    return tree

def run_tree_pricer(inp: Inputs) -> float:
    mkt = build_market(inp)
    opt = build_option(inp)
    tree = build_tree(inp, mkt, opt)

    # Si l’attribut interne 'tree' existe mais est vide, tente une construction tardive
    lattice = getattr(tree, "tree", None)
    if lattice is not None and not lattice:
        for method in ("build_tree", "build", "construct_tree", "construct", "init_tree", "initialize"):
            if hasattr(tree, method):
                try:
                    getattr(tree, method)()
                except TypeError:
                    try:
                        getattr(tree, method)(mkt, opt)
                    except TypeError:
                        pass
                break

    if inp.method == "rec" and hasattr(tree, "price_recursive"):
        return tree.price_recursive()
    else:
        return tree.price_backward()


def run_bs_pricer(inp: Inputs) -> Optional[float]:
    if inp.exercise != "EU":
        return None
    T_years = max((inp.maturity - inp.pricing_date).days, 0) / 365.0
    return bs_price(S=inp.spot, K=inp.strike, r=inp.rate, sigma=inp.vol,
                    T=T_years, is_call=(inp.cp == "Call"))
