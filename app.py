import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from models.market import Market
from models.option_trade import Option
from models.trinomial_tree import TrinomialTree
from utils.utils_bs import bs_price
from core_pricer import run_backward_pricing


# =============== PAGE SETUP ===============
st.set_page_config(page_title="Option Pricing App", layout="wide")

st.title("📈 Option Pricing — Trinomial Tree vs. Black–Scholes")
st.markdown("---")

# =============== TABS ===============
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "💹 Pricing", "📉 Sensitivity", "📊 Graphs"])

# =============== TAB 1 — HOME ===============
with tab1:
    st.header("Welcome 👋")
    st.markdown("""
    This app compares **Trinomial Tree** and **Black–Scholes** option pricing models.

    You can:
    - Adjust parameters interactively.
    - Run sensitivity tests for volatility, interest rate, and strike.
    - Visualize results dynamically.
    """)

# =============== TAB 2 — PRICING ===============
with tab2:
    st.header("💹 Compute Option Price")

    col1, col2 = st.columns(2)

    with col1:
        S0 = st.number_input("Spot Price (S₀)", value=100.0)
        K = st.number_input("Strike (K)", value=100.0)
        r = st.number_input("Interest Rate (r)", value=0.05)
        sigma = st.number_input("Volatility (σ)", value=0.2)
        T = st.number_input("Maturity (T, years)", value=1.0)
        N = st.slider("Number of Steps (N)", 10, 500, 100)

    with col2:
        is_call = st.radio("Option Type", ["Call", "Put"], horizontal=True) == "Call"
        exercise = st.radio("Exercise Style", ["european", "american"], horizontal=True)
        optimize = st.checkbox("Enable Pruning", value=False)
        threshold = st.number_input("Pruning Threshold", value=1e-6, format="%.1e")

    # Run models
    if st.button("Run Pricing"):
        market = Market(S0, r, sigma, T)
        option = Option(K, is_call)
        tree_price, elapsed, _ = run_backward_pricing(market, option, N, exercise, optimize, threshold)
        bs_val = bs_price(S0, K, r, sigma, T, is_call)

        st.success(f"✅ Tree Price: **{tree_price:.4f}**")
        st.info(f"📘 Black–Scholes: **{bs_val:.4f}**")
        st.caption(f"Time: {elapsed:.5f} sec")


# =============== TAB 3 — SENSITIVITY TESTS ===============
with tab3:
    st.header("📉 Sensitivity Tests")

    test_type = st.radio("Choose Parameter to Vary:", ["Volatility", "Interest Rate", "Strike"], horizontal=True)

    # Common inputs
    S0 = 100.0
    K = 100.0
    r = 0.05
    sigma = 0.2
    T = 1.0
    N = 100
    is_call = True
    exercise = "european"

    market = Market(S0, r, sigma, T)
    option = Option(K, is_call)

    if test_type == "Volatility":
        x_vals = np.linspace(0.01, 1.0, 80)
        param_name = "Volatility"
        x_label = "Volatility (σ)"
        bs_func = lambda s: bs_price(S0, K, r, s, T, is_call)
        tree_func = lambda s: run_backward_pricing(Market(S0, r, s, T), option, N, exercise, "Non", 1e-6)[0]

    elif test_type == "Interest Rate":
        x_vals = np.linspace(-0.1, 0.1, 80)
        param_name = "Interest Rate"
        x_label = "Interest Rate (r)"
        bs_func = lambda rr: bs_price(S0, K, rr, sigma, T, is_call)
        tree_func = lambda rr: run_backward_pricing(Market(S0, rr, sigma, T), option, N, exercise, "Non", 1e-6)[0]

    else:  # Strike
        x_vals = np.linspace(60, 140, 80)
        param_name = "Strike"
        x_label = "Strike (K)"
        bs_func = lambda kk: bs_price(S0, kk, r, sigma, T, is_call)
        tree_func = lambda kk: run_backward_pricing(Market(S0, r, sigma, T), Option(kk, is_call), N, exercise, "Non", 1e-6)[0]

    st.write(f"Running {param_name} Sensitivity...")

    bs_vals = np.array([bs_func(x) for x in x_vals])
    tree_vals = np.array([tree_func(x) for x in x_vals])
    diff = tree_vals - bs_vals

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_vals, diff, color="blue", lw=1.2, marker=".")
    ax.axhline(0, color="red", linestyle="--", lw=1)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Tree - BS")
    ax.set_title(f"Difference (Tree - BS) vs {param_name}")
    ax.grid(alpha=0.3)
    st.pyplot(fig)


# =============== TAB 4 — GRAPH VIEW ===============
with tab4:
    st.header("📊 Graph Output")

    st.markdown("""
    Here you can visualize the difference between **Trinomial Tree** and **Black–Scholes**
    across various parameters. Use the *Sensitivity* tab to generate the graphs.
    """)

    st.image("plots/last_diff_plot.png", caption="Last generated difference plot (if saved).")
