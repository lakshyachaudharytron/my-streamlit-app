import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

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
    integer_part = f"{number:.0f}"

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

    return f"-{formatted}" if is_negative else formatted

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
EMERALD = "#3FA66B"
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
# SENSITIVITY TABLE — IRR across Premium (% of Invested) x Years to Sell
# ============================================================
st.subheader("Sensitivity: IRR by Premium and Holding Period")
st.caption(
    "Rows = premium as a % of your total invested amount. Columns = years until sale. "
    "Each cell assumes your total invested amount is split evenly across that many years "
    "(custom installment amounts are not used here, so the grid stays well-defined for "
    "any number of years)."
)

def sensitivity_irr(total_invested_amt, premium_amt, n, rent_amt):
    if n <= 0 or total_invested_amt <= 0:
        return None
    if n == 1:
        # With a 1-year hold, installment and sale proceeds land in the same
        # period, so there's no discounting to solve for — the annualized
        # return is simply the profit over the amount invested.
        return (rent_amt + premium_amt) / total_invested_amt
    per_year = total_invested_amt / n
    cfs = [-per_year + rent_amt for _ in range(n - 1)]
    cfs.append(-per_year + rent_amt + (total_invested_amt + premium_amt))
    return calculate_irr(cfs)

premium_pct_rows = [10, 20, 30, 40, 50, 75, 100]
years_cols = list(range(1, max(8, n_years + 3) + 1))

sens_data = np.full((len(premium_pct_rows), len(years_cols)), np.nan)
for r_idx, pct in enumerate(premium_pct_rows):
    premium_amt = total_invested * (pct / 100)
    for c_idx, y in enumerate(years_cols):
        irr_val = sensitivity_irr(total_invested, premium_amt, y, annual_rent)
        if irr_val is not None:
            sens_data[r_idx, c_idx] = irr_val * 100

sens_cmap = LinearSegmentedColormap.from_list("sens_cmap", [ROSE, PANEL_DARK, EMERALD])

# Anchor the color scale so 10% IRR is the crossover point: anything below
# 10% leans red, anything above gradually leans greener as it climbs toward
# the highest value actually in the grid (rather than requiring 100%+ to
# register as green).
valid_vals = sens_data[~np.isnan(sens_data)]
data_min = float(valid_vals.min()) if valid_vals.size else 0.0
data_max = float(valid_vals.max()) if valid_vals.size else 20.0
sens_vmin = min(data_min, 9.0)
sens_vmax = max(data_max, 11.0)
sens_norm = TwoSlopeNorm(vmin=sens_vmin, vcenter=10.0, vmax=sens_vmax)

fig_sens, ax_sens = plt.subplots(figsize=(1.1 + len(years_cols) * 0.85, 1.1 + len(premium_pct_rows) * 0.62))
fig_sens.patch.set_facecolor(BG_DARK)
ax_sens.set_facecolor(PANEL_DARK)

im = ax_sens.imshow(sens_data, cmap=sens_cmap, aspect="auto", norm=sens_norm)

ax_sens.set_xticks(range(len(years_cols)))
ax_sens.set_xticklabels([f"Yr {y}" for y in years_cols], color=TEXT_LIGHT, fontsize=9)
ax_sens.set_yticks(range(len(premium_pct_rows)))
ax_sens.set_yticklabels([f"{p}%" for p in premium_pct_rows], color=TEXT_LIGHT, fontsize=9)
ax_sens.set_xlabel("Years to Sell", color=TEXT_LIGHT)
ax_sens.set_ylabel("Premium (% of Invested)", color=TEXT_LIGHT)
ax_sens.set_title("IRR Sensitivity (%)", color=TITLE_LIGHT, fontsize=12, pad=10)
for spine in ax_sens.spines.values():
    spine.set_visible(False)

for r_idx in range(len(premium_pct_rows)):
    for c_idx in range(len(years_cols)):
        val = sens_data[r_idx, c_idx]
        text = f"{val:.0f}%" if not np.isnan(val) else "N/A"
        ax_sens.text(c_idx, r_idx, text, ha="center", va="center", color="#FFFFFF",
                     fontsize=8.5, fontweight="bold")

cbar = fig_sens.colorbar(im, ax=ax_sens, fraction=0.046, pad=0.03)
cbar.ax.tick_params(colors=TEXT_LIGHT, labelsize=8)
cbar.set_label("IRR (%)", color=TEXT_LIGHT)
cbar.outline.set_edgecolor(BORDER)

st.pyplot(fig_sens)

# ============================================================
# BREAK-EVEN PREMIUM — minimum premium needed to match a benchmark's return
# ============================================================
st.subheader("Break-Even Premium vs. a Benchmark")
st.caption(
    "For each holding period, this shows the minimum premium you'd need to match a "
    "chosen benchmark's annual return — using the same even-split installment assumption "
    "as the sensitivity grid above."
)

breakeven_benchmark = st.selectbox(
    "Compare against", list(benchmark_rates.keys()), key="breakeven_benchmark"
)
target_rate = benchmark_rates[breakeven_benchmark] / 100

def required_premium(total_invested_amt, n, rent_amt, target_r):
    if n <= 0:
        return None
    if n == 1:
        # Matches the sensitivity_irr special case: for a 1-year hold,
        # solve premium directly from (rent + premium) / invested = target_r.
        return target_r * total_invested_amt - rent_amt
    per_year = total_invested_amt / n
    last_year_pre_premium_cf = -per_year + rent_amt
    a_sum = sum((last_year_pre_premium_cf) / (1 + target_r) ** i for i in range(n - 1))
    premium_needed = -a_sum * (1 + target_r) ** (n - 1) - last_year_pre_premium_cf - total_invested_amt
    return premium_needed

required_premiums = [
    required_premium(total_invested, y, annual_rent, target_rate) for y in years_cols
]

fig_be, ax_be = make_dark_fig(figsize=(7, 4))
ax_be.plot(years_cols, [p / 1e7 for p in required_premiums], color=STEEL, marker="o",
           linewidth=2, markersize=5, label=f"Break-even vs {breakeven_benchmark}")

# Highlight the user's actual premium at their chosen years_to_sell
if n_years in years_cols:
    be_at_selected = required_premiums[years_cols.index(n_years)]
    user_color = TEAL if selected_premium >= be_at_selected else ROSE
    ax_be.scatter([n_years], [selected_premium / 1e7], color=user_color, s=90, zorder=5,
                  edgecolor=BG_DARK, label="Your premium & years")

ax_be.set_xlabel("Years to Sell")
ax_be.set_ylabel("Premium Needed (₹ Cr)")
ax_be.set_xticks(years_cols)
ax_be.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}"))
ax_be.set_title(f"Premium Needed to Match {breakeven_benchmark}", fontsize=12, pad=10)
legend = ax_be.legend(facecolor=PANEL_DARK, edgecolor=BORDER, labelcolor=TEXT_LIGHT, fontsize=8.5)
st.pyplot(fig_be)

if n_years in years_cols:
    if selected_premium >= be_at_selected:
        st.write(
            f"**Your premium (₹{format_indian(selected_premium)}) beats {breakeven_benchmark}** "
            f"at {n_years} years — it only needed ₹{format_indian(be_at_selected)}."
        )
    else:
        st.write(
            f"**Your premium (₹{format_indian(selected_premium)}) falls short of {breakeven_benchmark}** "
            f"at {n_years} years — you'd need ₹{format_indian(be_at_selected)} to match it."
        )

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
