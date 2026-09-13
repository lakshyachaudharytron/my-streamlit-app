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
        return None  # no sign change -> IRR not solvable in this range
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

# ---------- Inputs ----------
st.subheader("Investment Details")

initial_investment = st.number_input(
    "Initial Investment (Total Property Value, ₹)",
    min_value=0.0, value=10000000.0, step=100000.0, format="%.2f"
)

pct_paid = st.slider("% Paid So Far / Committed (%)", min_value=1, max_value=100, value=50)
total_paid = initial_investment * (pct_paid / 100)
st.write(f"**Total Paid:** ₹{total_paid:,.2f}")

years_to_sell = st.number_input(
    "Total Years Until Investment is Sold", min_value=1, max_value=30, value=5, step=1
)

st.subheader("Appreciation Scenarios (Annual %)")
col1, col2, col3 = st.columns(3)
with col1:
    bullish_rate = st.number_input("Bullish (%)", value=15.0, step=0.5)
with col2:
    normal_rate = st.number_input("Normal (%)", value=10.0, step=0.5)
with col3:
    bearish_rate = st.number_input("Bearish (%)", value=5.0, step=0.5)

scenario = st.selectbox("Select Scenario to Calculate", ["Bullish", "Normal", "Bearish"])
rate_map = {"Bullish": bullish_rate, "Normal": normal_rate, "Bearish": bearish_rate}
selected_rate = rate_map[scenario] / 100

# ---------- Cash Flow Construction ----------
# Payments are spread evenly over the years until sale (year 0 to years_to_sell - 1)
annual_payment = total_paid / years_to_sell
cash_flows = [-annual_payment for _ in range(years_to_sell)]

# Property value appreciates on the FULL initial investment (not just amount paid),
# since ownership rights typically track full unit value once booked
sale_value = initial_investment * (1 + selected_rate) ** years_to_sell
cash_flows.append(sale_value)

irr = calculate_irr(cash_flows)

# ---------- Results ----------
st.subheader("Results")
st.write(f"**Annual Payment (spread evenly):** ₹{annual_payment:,.2f}")
st.write(f"**Projected Sale Value ({scenario} scenario, Year {years_to_sell}):** ₹{sale_value:,.2f}")

if irr is not None:
    st.metric("IRR", f"{irr * 100:.2f}%")
else:
    st.error("IRR could not be calculated for these inputs (try adjusting values).")

with st.expander("Cash Flow Breakdown"):
    for i, cf in enumerate(cash_flows):
        label = "Payment" if cf < 0 else "Sale Proceeds"
        st.write(f"Year {i}: {label} — ₹{cf:,.2f}")
