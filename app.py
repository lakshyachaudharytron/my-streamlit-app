import streamlit as st

st.set_page_config(page_title="Real Estate IRR Calculator", layout="centered")

# ---------- Teal theme CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}
h1 {
    color: #14B8A6;
    font-weight: 700;
    letter-spacing: -0.02em;
    border-bottom: 2px solid #1E293B;
    padding-bottom: 0.6rem;
    margin-bottom: 1.5rem;
}
h3 {
    color: #FFFFFF;
    font-weight: 600;
    margin-top: 2rem;
}
[data-testid="stMarkdownContainer"] p strong {
    font-family: 'JetBrains Mono', monospace;
    color: #14B8A6;
}
[data-testid="stMetric"] {
    background-color: #1E293B;
    border: 1px solid #0F6E68;
    border-left: 4px solid #14B8A6;
    border-radius: 6px;
    padding: 1rem 1.25rem;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace;
    color: #14B8A6;
    font-weight: 600;
}
[data-testid="stExpander"] {
    border: 1px solid #1E293B;
    border-radius: 6px;
}
[data-testid="stCaptionContainer"] {
    color: #94A3B8;
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

# ============================================================
# INPUTS
# ============================================================
st.subheader("Investment Details")

initial_investment = currency_text_input(
    "Initial Investment (Total Property Value, ₹)", "initial_investment", 10000000.0
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
# SCENARIO PREMIUMS — Bullish / Normal / Bearish
# ============================================================
st.subheader("Scenario Premiums — Bullish / Normal / Bearish")
st.caption("Each scenario is a flat ₹ premium added on top of the appreciated value above.")

bullish_premium = currency_text_input("Bullish Premium (₹)", "bullish_premium", 2000000.0)
normal_premium = currency_text_input("Normal Premium (₹)", "normal_premium", 1000000.0)
bearish_premium = currency_text_input("Bearish Premium (₹)", "bearish_premium", 0.0)

scenario = st.selectbox("Select Scenario to Calculate", ["Bullish", "Normal", "Bearish"])
premium_map = {"Bullish": bullish_premium, "Normal": normal_premium, "Bearish": bearish_premium}
selected_premium = premium_map[scenario]

sale_value = appreciated_value + selected_premium

# ============================================================
# CASH FLOW CONSTRUCTION
# ============================================================
# Each year: -installment + rent (rent is 0 if toggle is off)
# Final year additionally nets the sale value in
cash_flows = [-installments[i] + annual_rent for i in range(int(years_to_sell) - 1)]
final_year_cashflow = (sale_value - installments[-1]) + annual_rent
cash_flows.append(final_year_cashflow)

irr = calculate_irr(cash_flows)

# ============================================================
# RESULTS
# ============================================================
st.subheader("Results")
st.write(f"**Appreciated Value (Year {years_to_sell}, before premium):** ₹{format_indian(appreciated_value)}")
st.write(f"**{scenario} Premium:** ₹{format_indian(selected_premium)}")
st.write(f"**Final Sale Value (Appreciated Value + Premium):** ₹{format_indian(sale_value)}")
if use_rental_income:
    st.write(f"**Annual Rent (included every year):** ₹{format_indian(annual_rent)}")
st.write(f"**Final Year Net Cash Flow (Sale − Last Installment + Rent):** ₹{format_indian(final_year_cashflow)}")

if irr is not None:
    st.metric("IRR", f"{irr * 100:.2f}%")
else:
    st.error("IRR could not be calculated for these inputs (try adjusting values).")

with st.expander("Cash Flow Breakdown (Year by Year)"):
    for i, cf in enumerate(cash_flows):
        label = "Installment + Rent" if i < int(years_to_sell) - 1 else "Sale − Last Installment + Rent (net)"
        st.write(f"Year {i}: {label} — ₹{format_indian(cf)}")

# ============================================================
# OPTIONAL: Year-by-year growth of the appreciated value (toggle ON only)
# ============================================================
if use_appreciation_rate:
    show_yearly = st.checkbox("Show year-by-year appreciation (before premium)")
    if show_yearly:
        st.subheader("Year-by-Year Appreciated Value")
        for year in range(int(years_to_sell) + 1):
            year_value = initial_investment * (1 + rate) ** year
            st.write(f"Year {year}: ₹{format_indian(year_value)}")
