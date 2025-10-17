import streamlit as st
from models.market import Market, DividendPolicy
from models.option_trade import Option
from models.tree import TrinomialTree

st.set_page_config(page_title="Trinomial Tree Option Pricer", page_icon="📈")

st.title("📈 Option Pricing – Trinomial Tree Model")
st.markdown("Use the panel below to set market and option parameters.")

# --- Sidebar inputs ---
st.sidebar.header("Market parameters")
S0 = st.sidebar.number_input("Initial stock price (S₀)", value=100.0, step=1.0)
r = st.sidebar.number_input("Risk-free rate (r)", value=0.02, step=0.005, format="%.3f")
sigma = st.sidebar.number_input("Volatility (σ)", value=0.25, step=0.01, format="%.3f")
T = st.sidebar.number_input("Maturity (years)", value=1.0, step=0.25)
N = st.sidebar.slider("Number of steps (N)", 5, 200, 50)

# --- Dividend section ---
st.sidebar.subheader("Dividends")
has_div = st.sidebar.checkbox("Include discrete dividend?")
dividends = []
if has_div:
    t_div = st.sidebar.number_input("Ex-dividend time (in years)", value=0.25, step=0.05)
    rho = st.sidebar.number_input("Dividend intensity ρ", value=0.03, step=0.01)
    lam = st.sidebar.number_input("Transition speed λ", value=0.5, step=0.1)
    dividends.append((t_div, DividendPolicy(rho=rho, lam=lam)))

# --- Option parameters ---
st.sidebar.header("Option parameters")
K = st.sidebar.number_input("Strike price (K)", value=100.0, step=1.0)
option_type = st.sidebar.selectbox("Type", ["call", "put"])
exercise = st.sidebar.selectbox("Exercise style", ["european", "american"])

is_call = True if option_type.lower() == "call" else False

# --- Run pricing ---
if st.button("Compute option price"):
    # Build market, option, tree
    mkt = Market(S0=S0, r=r, sigma=sigma, T=T, dividends=dividends)
    opt = Option(K=K, T=T, is_call=is_call)
    tree = TrinomialTree(market=mkt, option=opt, N=N, exercise=exercise)

    tree.build_tree()
    price = tree.price()

    st.success(f"💰 Option price: **{price:.4f}**")

    # Optional: show trunk evolution
    st.subheader("Trunk evolution (mid-node prices)")
    trunk_data = [(i * tree.dt, tree.trunk[i]) for i in range(len(tree.trunk))]
    st.dataframe({"t (years)": [round(t, 3) for t, _ in trunk_data],
                  "Mid price": [round(S, 4) for _, S in trunk_data]})

    st.line_chart({ "Mid price": [S for _, S in trunk_data] })

else:
    st.info("👈 Fill the parameters and click *Compute option price*")
