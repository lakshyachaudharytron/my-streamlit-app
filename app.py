import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

st.set_page_config(page_title="Real Estate IRR Calculator", layout="centered")

# ---------- Classy theme CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

html, body, [class*="css"]  {
    font-family: 'Source Sans 3', sans-serif;
}
.stApp {
    background-color: #0B0F14;
}
h1 {
    font-family: 'Playfair Display', serif;
    color: #D8B36A;
    font-weight: 700;
    letter-spacing: -0.01em;
    border-bottom: 2px solid #2A3240;
    padding-bottom: 0.7rem;
    margin-bottom: 1.6rem;
}
h3 {
    font-family: 'Playfair Display', serif;
    color: #EDEBE5;
    font-weight: 600;
    letter-spacing: 0.01em;
    margin-top: 2.2rem;
}
[data-testid="stMarkdownContainer"] p strong {
    font-family: 'JetBrains Mono', monospace;
    color: #D8B36A;
}
[data-testid="stMetric"] {
    background-color: #151A22;
    border: 1px solid #2A3240;
    border-left: 4px solid #D8B36A;
    border-radius: 8px;
    padding: 1.1rem 1.35rem;
    box-shadow: 0 3px 12px rgba(0,0,0,0.3);
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace;
    color: #D8B36A;
    font-weight: 600;
}
[data-testid="stMetricLabel"] {
    color: #A9B1BC;
}
[data-testid="stExpander"] {
    border: 1px solid #2A3240;
    border-radius: 8px;
    background-color: #10141B;
}
[data-testid="stCaptionContainer"] {
    color: #8D97A3;
    font-style: italic;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5rem 0 1rem 0;
}
table thead th {
    background-color: #151A22;
    color: #D8B36A;
    font-family: 'Playfair Display', serif;
    font-weight: 600;
    text-align: left;
    padding: 0.65rem 0.9rem;
    border-bottom: 2px solid #D8B36A;
}
table tbody td {
    padding: 0.6rem 0.9rem;
    border-bottom: 1px solid #232A34;
    color: #E5E3DD;
}
table tbody tr:nth-child(even) {
    background-color: #10141B;
}
</style>
""", unsafe_allow_html=True)

st.title("Under-Construction Real Estate — IRR Calculator")

# ---------- IRR helper (pure Python, no extra dependencies) ----------
def npv(rate, cash_flows):
    return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

def calculate_irr(cash_flows, low=-0.99, high=10.0, tol=1e-6, max_iter=1000):
    f_low = npv(low, cash_flows)
    f_high = npv(high, cash_flows)
    if f_low * f_high > 0:
        return None
    for _ in range(max_iter):
        mid = (low + high) / 2
        f_mid = npv(mid, cash_flows)
        if abs(f_mid) < tol:
            return mid
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return mid

# ---------- Indian numbering system formatter (lakhs/crores) ----------
def format_indian(number):
    is_negative = number < 0
    number = abs(number)
    s = f"{number:.2f}"
    integer_part, decimal_part = s.split(".")

    if len(integer_part) <= 3:
        formatted = integer_part
    else:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        formatted = ",".join(parts) + "," + last_three

    result = f"{formatted}.{decimal_part}"
    return f"-{result}" if is_negative else result

def parse_indian(text):
    raw = text.replace(",", "").replace("₹", "").strip()
    if raw == "":
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0

def currency_text_input(label, key, default_value):
    if key not in st.session_state:
        st.session_state[key] = format_indian(default_value)

    def _reformat():
        value = parse_indian(st.session_state[key])
        st.session_state[key] = format_indian(value)

    st.text_input(label, key=key, on_change=_reformat)
    return parse_indian(st.session_state[key])

# ---------- Matplotlib styling to match the app's dark/gold theme ----------
GOLD = "#D8B36A"
TEAL = "#4C9A8E"
ROSE = "#C0596B"
STEEL = "#5C7A99"
TEXT_LIGHT = "#C7CDD6"
TITLE_LIGHT = "#EDEBE5"
GRID_LINE = "#232A34"
BG_DARK = "#0B0F14"
PANEL_DARK = "#10141B"
BORDER = "#2A3240"

plt.rcParams["font.family"] = "serif"

def make_dark_fig(figsize=(7, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(PANEL_DARK)
    ax.tick_params(colors=TEXT_LIGHT, labelsize=9)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(BORDER)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.title.set_color(TITLE_LIGHT)
    ax.xaxis.label.set_color(TEXT_LIGHT)
    ax.yaxis.label.set_color(TEXT_LIGHT)
    ax.grid(axis="x" if ax.get_ylabel() == "" else "y", color=GRID_LINE, linewidth=0.6, alpha=0.7)
    return fig, ax

# ============================================================
# INPUTS
# ============================================================
st.subheader("Investment Details")

initial_investment = currency_text_input(
    "Property Value (₹)", "initial_investment", 10000000.0
)

pct_paid = st.slider("% Paid So Far / Committed (%)", min_value=1, max_value=100, value=50)
total_paid = initial_investment * (pct_paid / 100)
st.write(f"**Total Paid (based on % Paid):** ₹{format_indian(total_paid)}")

years_to_sell = st.number_input(
    "Total Years Until Investment is Sold", min_value=1, max_value=30, value=5, step=1
)

# ============================================================
# INSTALLMENT SCHEDULE — even split (default) vs custom per-year
# ============================================================
st.subheader("Installment Schedule")

use_custom_installments = st.toggle("Enter custom installment amount for each year (instead of splitting evenly)")

if use_custom_installments:
    st.caption(f"Enter the installment for each of the {years_to_sell} year(s):")
    default_even_split = total_paid / years_to_sell
    installments = []
    for year in range(int(years_to_sell)):
        amount = currency_text_input(
            f"Year {year} Installment (₹)", f"installment_year_{year}", default_even_split
        )
        installments.append(amount)
    total_paid_actual = sum(installments)
    st.write(f"**Total Paid (sum of custom installments):** ₹{format_indian(total_paid_actual)}")
else:
    installments = [total_paid / years_to_sell for _ in range(int(years_to_sell))]
    total_paid_actual = total_paid

# ============================================================
# RENTAL INCOME — optional, applied every year up to and including sale year
# ============================================================
st.subheader("Rental Income")

use_rental_income = st.toggle("Include annual rental income in the cash flow")

if use_rental_income:
    annual_rent = currency_text_input("Annual Rent Received (₹)", "annual_rent", 300000.0)
    st.caption(f"This rent will be added as income for every year, including Year {years_to_sell} (the sale year).")
else:
    annual_rent = 0.0

# ============================================================
# ANNUAL APPRECIATION — independent of scenarios, compounds every year
# ============================================================
st.subheader("Annual Appreciation of Investment Value")

use_appreciation_rate = st.toggle("Grow the investment value every year using an appreciation rate")

if use_appreciation_rate:
    appreciation_rate = st.slider("Annual Appreciation Rate (%)", 0.0, 30.0, 10.0, 0.5)
    rate = appreciation_rate / 100
    appreciated_value = initial_investment * (1 + rate) ** years_to_sell
else:
    rate = 0.0
    appreciated_value = initial_investment

st.write(f"**Appreciated Value at Year {years_to_sell} (before scenario premium):** ₹{format_indian(appreciated_value)}")

# ============================================================
# PREMIUM
# ============================================================
st.subheader("Premium")
st.caption("A flat ₹ premium on top of what you've paid so far.")

selected_premium = currency_text_input("Premium (₹)", "premium", 2000000.0)

# ============================================================
# NET SALE PROCEEDS
# ============================================================
# When you sell/assign an under-construction allotment before possession,
# you receive back what you've already paid the builder, plus your premium.
# The buyer separately takes over whatever remains owed to the builder.
net_sale_proceeds = total_paid_actual + selected_premium

# ============================================================
# CASH FLOW CONSTRUCTION
# ============================================================
# Each year: -installment + rent (rent is 0 if toggle is off)
# Final year additionally nets in the NET sale proceeds (not the raw market value)
cash_flows = [-installments[i] + annual_rent for i in range(int(years_to_sell) - 1)]
final_year_cashflow = -installments[-1] + annual_rent + net_sale_proceeds
cash_flows.append(final_year_cashflow)

irr = calculate_irr(cash_flows)

# ============================================================
# ROI CALCULATION
# ============================================================
total_invested = sum(installments)  # = total_paid_actual, what you actually paid out of pocket
total_rent_collected = annual_rent * int(years_to_sell)
total_returns = net_sale_proceeds + total_rent_collected
net_profit = total_returns - total_invested
roi = (net_profit / total_invested) * 100 if total_invested > 0 else 0.0

# ============================================================
# RESULTS
# ============================================================
st.subheader("Results")
st.write(f"**Appreciated Value (Year {years_to_sell}, before premium):** ₹{format_indian(appreciated_value)}")
st.write(f"**Total Paid:** ₹{format_indian(total_paid_actual)}")
st.write(f"**Premium:** ₹{format_indian(selected_premium)}")
st.write(f"**Net Sale Proceeds (Total Paid + Premium):** ₹{format_indian(net_sale_proceeds)}")
if use_rental_income:
    st.write(f"**Annual Rent (included every year):** ₹{format_indian(annual_rent)}")
    st.write(f"**Total Rent Collected (over {years_to_sell} years):** ₹{format_indian(total_rent_collected)}")
st.write(f"**Total Invested (out of pocket):** ₹{format_indian(total_invested)}")
st.write(f"**Total Returns (Net Sale Proceeds + Rent):** ₹{format_indian(total_returns)}")
st.write(f"**Net Profit:** ₹{format_indian(net_profit)}")

col_irr, col_roi = st.columns(2)
with col_irr:
    if irr is not None:
        st.metric("IRR (Annualized)", f"{irr * 100:.2f}%")
    else:
        st.error("IRR could not be calculated (try adjusting values).")
with col_roi:
    st.metric("ROI (Total, Non-Annualized)", f"{roi:.2f}%")

with st.expander("Cash Flow Breakdown (Year by Year)"):
    for i, cf in enumerate(cash_flows):
        label = "Installment + Rent" if i < int(years_to_sell) - 1 else "Net Sale Proceeds − Last Installment + Rent"
        st.write(f"Year {i}: {label} — ₹{format_indian(cf)}")

# ============================================================
# BENCHMARK COMPARISON — static reference figures
# ============================================================
st.subheader("Benchmark Annual Returns (for comparison)")
st.caption("Historical figures as of mid-to-late 2026. Past performance does not guarantee future returns.")

st.markdown("""
| Benchmark | Annual Return (CAGR) |
|---|---|
| Nifty 50 (5-Year) | ~11.7% |
| Nifty 50 (10-Year) | ~13.4% |
| Nifty Realty Index (5-Year) | ~20.6% |
| Nifty Realty Index (1-Year) | ~-4% to -8% (volatile) |
| Gold — India (10-Year) | ~10–11% |
| Gold — India (5-Year) | ~10–17% (recent rally skews this higher) |
| Bank FD (current, 1–5 Yr) | ~6.5–7.1% |
| NHB RESIDEX — Delhi (official index) | ~0–6% |
| Gurgaon Capital Values (JLL, 2025) | ~12.5% |
| Delhi-NCR Avg. Price (Anarock, 2025) | ~23% |
""")

# ============================================================
# "WHAT IF YOU INVESTED THE SAME INSTALLMENTS ELSEWHERE?"
# ============================================================
# Each installment is treated as a contribution made at that year, which then
# compounds annually (at the benchmark's CAGR) along with everything invested
# before it, right up to the year of sale. The final year's installment does
# not get an extra year of growth, since it's paid right at the point of sale.
#
# Example: installments of 20, 10, 30 at a rate r:
#   Year 1: 20 grows -> 20*(1+r)
#   Year 2: add 10 -> (20*(1+r) + 10), this then grows -> *(1+r)
#   Year 3: add 30 -> final value (no further growth, this is the sale year)

st.subheader("Your Deal vs. The Alternatives")
st.caption(
    "Assumes each installment is invested the year it's paid and compounds "
    "annually at the benchmark's return, right up to the year you sell. "
    "Your real estate return (IRR) is shown alongside for direct comparison."
)

benchmark_rates = {
    "Nifty 50 (5-Year)": 11.7,
    "Nifty 50 (10-Year)": 13.4,
    "Nifty Realty Index (5-Year)": 20.6,
    "Nifty Realty Index (1-Year)": -6.0,
    "Gold — India (10-Year)": 10.5,
    "Gold — India (5-Year)": 13.5,
    "Bank FD (current, 1–5 Yr)": 6.8,
    "NHB RESIDEX — Delhi": 3.0,
    "Gurgaon Capital Values (JLL, 2025)": 12.5,
    "Delhi-NCR Avg. Price (Anarock, 2025)": 23.0,
}

n_years = int(years_to_sell)

def compounded_value(cash_amounts, annual_rate_pct, n):
    r = annual_rate_pct / 100
    balance = 0.0
    for i in range(n):
        balance += cash_amounts[i]
        if i < n - 1:
            balance *= (1 + r)
    return balance

comparison_table_md = "| Investment | Annual Return | Final Value |\n|---|---|---|\n"
for name, pct in benchmark_rates.items():
    fv = compounded_value(installments, pct, n_years)
    comparison_table_md += f"| {name} | {pct:.1f}% | ₹{format_indian(fv)} |\n"

st.markdown(comparison_table_md)
st.caption(f"Based on the same ₹{format_indian(total_invested)} invested across your installment schedule.")

st.markdown("#### Final Value — Your Deal vs. Alternatives")
compare_names = ["Your Real Estate Deal"] + list(benchmark_rates.keys())
compare_values = [net_sale_proceeds] + [
    compounded_value(installments, pct, n_years) for pct in benchmark_rates.values()
]
compare_colors = [GOLD] + [STEEL] * len(benchmark_rates)
sorted_rows = sorted(zip(compare_names, compare_values, compare_colors), key=lambda r: r[1])
sorted_names, sorted_values, sorted_colors = zip(*sorted_rows)

fig_cmp, ax_cmp = make_dark_fig(figsize=(7, 5))
ax_cmp.barh(sorted_names, [v / 1e7 for v in sorted_values], color=sorted_colors, height=0.6)
ax_cmp.set_xlabel("Final Value (₹ Cr)")
ax_cmp.set_title("Final Value Comparison (gold = your deal)", fontsize=12, pad=10)
ax_cmp.grid(axis="x", color=GRID_LINE, linewidth=0.6, alpha=0.7)
ax_cmp.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}"))
st.pyplot(fig_cmp)

with st.expander("Year-by-Year Compounding Detail (per benchmark)"):
    detail_benchmark = st.selectbox("Choose a benchmark to see the year-by-year build-up", list(benchmark_rates.keys()))
    r_detail = benchmark_rates[detail_benchmark] / 100
    running_balance = 0.0
    for i in range(n_years):
        running_balance += installments[i]
        label = f"Year {i}: + ₹{format_indian(installments[i])} → Balance before growth: ₹{format_indian(running_balance)}"
        if i < n_years - 1:
            running_balance *= (1 + r_detail)
            label += f" → After {detail_benchmark} growth: ₹{format_indian(running_balance)}"
        else:
            label += " → (sale year, no further growth)"
        st.write(label)
    st.write(f"**Final Compounded Value ({detail_benchmark}):** ₹{format_indian(running_balance)}")

# ============================================================
# OPTIONAL: Year-by-year growth of the appreciated value (toggle ON only)
# ============================================================
if use_appreciation_rate:
    show_yearly = st.checkbox("Show year-by-year appreciation (before premium)")
    if show_yearly:
        st.subheader("Year-by-Year Appreciated Value")

        yrs_range = list(range(int(years_to_sell) + 1))
        vals_range = [initial_investment * (1 + rate) ** y for y in yrs_range]

        fig_app, ax_app = make_dark_fig(figsize=(7, 3.8))
        ax_app.plot(yrs_range, [v / 1e7 for v in vals_range], color=GOLD, marker="o",
                    linewidth=2, markersize=5, markerfacecolor=GOLD, markeredgecolor=BG_DARK)
        ax_app.fill_between(yrs_range, [v / 1e7 for v in vals_range], color=GOLD, alpha=0.08)
        ax_app.set_xlabel("Year")
        ax_app.set_ylabel("Property Value (₹ Cr)")
        ax_app.set_xticks(yrs_range)
        ax_app.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}"))
        ax_app.set_title("Property Value Appreciation Over Time", fontsize=12, pad=10)
        st.pyplot(fig_app)

        for year in yrs_range:
            year_value = initial_investment * (1 + rate) ** year
            st.write(f"Year {year}: ₹{format_indian(year_value)}")
