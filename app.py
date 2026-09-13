import streamlit as st

st.set_page_config(page_title="Real Estate IRR Calculator", layout="centered")
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

# ---------- Reusable comma-formatted currency text input ----------
def currency_text_input(label, key, default_value):
    if key not in st.session_state:
        st.session_state[key] = format_indian(default_value)

    def _reformat():
        value = parse_indian(st.session_state[key])
        st.session_state[key] = format_indian(value)

    st.text_input(label, key=key, on_change=_reformat)
    return parse_indian(st.session_state[key])

# ---------- Inputs ----------
st.subheader("Investment Details")

initial_investment = currency_text_input(
    "Initial Investment (Total Property Value, ₹)", "initial_investment", 10000000.0
)

pct_paid = st.slider("% Paid So Far / Committed (%)", min_value=1, max_value=100, value=50)
total_paid = initial_investment * (pct_paid / 100)
st.write(f"**Total Paid:** ₹{format_indian(total_paid)}")

years_to_sell = st.number_input(
    "Total Years Until Investment is Sold", min_value=1, max_value=30, value=5, step=1
)

st.subheader("Scenario Inputs")

input_mode = st.radio(
    "How do you want to define Bullish / Normal / Bearish?",
    ["Absolute Sale Value (₹)", "Annual Appreciation Rate (%)"],
)

if input_mode == "Absolute Sale Value (₹)":
    bullish_value = currency_text_input("Bullish — Expected Sale Value (₹)", "bullish_value", 18000000.0)
    normal_value = currency_text_input("Normal — Expected Sale Value (₹)", "normal_value", 15000000.0)
    bearish_value = currency_text_input("Bearish — Expected Sale Value (₹)", "bearish_value", 12000000.0)

    scenario = st.selectbox("Select Scenario to Calculate", ["Bullish", "Normal", "Bearish"])
    value_map = {"Bullish": bullish_value, "Normal": normal_value, "Bearish": bearish_value}
    sale_value = value_map[scenario]

    if initial_investment > 0 and years_to_sell > 0:
        implied_rate = (sale_value / initial_investment) ** (1 / years_to_sell) - 1
    else:
        implied_rate = 0.0

else:  # Annual Appreciation Rate mode
    st.write("Set Annual Appreciation Rate (%) for each scenario:")
    bullish_rate = st.slider("Bullish Annual Appreciation Rate (%)", min_value=0.0, max_value=30.0, value=15.0, step=0.5)
    normal_rate = st.slider("Normal Annual Appreciation Rate (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
    bearish_rate = st.slider("Bearish Annual Appreciation Rate (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.5)

    scenario = st.selectbox("Select Scenario to Calculate", ["Bullish", "Normal", "Bearish"])
    rate_map = {"Bullish": bullish_rate, "Normal": normal_rate, "Bearish": bearish_rate}
    implied_rate = rate_map[scenario] / 100

    sale_value = initial_investment * (1 + implied_rate) ** years_to_sell

# ---------- Cash Flow Construction ----------
# Payments spread evenly over the years until sale; final year nets the last
# installment against the sale proceeds (sale happens same year as last payment).
annual_payment = total_paid / years_to_sell
cash_flows = [-annual_payment for _ in range(years_to_sell - 1)]
cash_flows.append(sale_value - annual_payment)

irr = calculate_irr(cash_flows)

# ---------- Results ----------
st.subheader("Results")
st.write(f"**Annual Payment (spread evenly):** ₹{format_indian(annual_payment)}")
st.write(f"**Sale Value ({scenario} scenario, Year {years_to_sell}):** ₹{format_indian(sale_value)}")
st.write(f"**Annual Appreciation Rate ({'implied' if input_mode.startswith('Absolute') else 'input'}):** {implied_rate * 100:.2f}%")

if irr is not None:
    st.metric("IRR", f"{irr * 100:.2f}%")
else:
    st.error("IRR could not be calculated for these inputs (try adjusting values).")

with st.expander("Cash Flow Breakdown"):
    for i, cf in enumerate(cash_flows):
        label = "Payment" if i < years_to_sell - 1 else "Sale Proceeds − Final Payment (net)"
        st.write(f"Year {i}: {label} — ₹{format_indian(cf)}")

# ---------- Optional year-by-year appreciation table ----------
show_yearly = st.checkbox("Show year-by-year appreciation")
if show_yearly:
    st.subheader("Year-by-Year Property Value")
    for year in range(years_to_sell + 1):
        year_value = initial_investment * (1 + implied_rate) ** year
        st.write(f"Year {year}: ₹{format_indian(year_value)}")
