import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Set the title
st.title("Bond Price vs Yield to Maturity")

# Initialize session state to store curves
if 'curves' not in st.session_state:
    st.session_state.curves = []
    st.session_state.last_maturity = None

# Sidebar inputs
st.sidebar.header("Bond Parameters")

# Coupon rate input (0% to 10% in increments of 0.25%)
coupon_rate = st.sidebar.slider("Coupon Rate (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.25)

# Coupon frequency (annual or semi-annual)
coupon_frequency = st.sidebar.selectbox("Coupon Frequency", ["Annual", "Semi-Annual"])

# Remaining maturity input (0.5 to 30 years in 0.5-year steps)
maturity = st.sidebar.slider("Maturity (Years)", min_value=0.5, max_value=30.0, value=10.0, step=0.5)

# Reset button
reset = st.sidebar.button("Reset Chart")

# Constants
face_value = 100

# Determine periods and coupon payment
if coupon_frequency == "Annual":
    periods_per_year = 1
else:
    periods_per_year = 2

n_periods = int(maturity * periods_per_year)
coupon_payment = face_value * (coupon_rate / 100) / periods_per_year

# Generate yields to maturity (0.1% to 20%)
yields = np.linspace(0.001, 0.2, 500)
prices = []

# Calculate bond prices for each yield
def calculate_bond_price(yield_rate):
    return sum([coupon_payment / (1 + yield_rate / periods_per_year) ** t for t in range(1, n_periods + 1)]) + \
           face_value / (1 + yield_rate / periods_per_year) ** n_periods

for ytm in yields:
    price = calculate_bond_price(ytm)
    prices.append(price)

# Reset or update curves
if reset or (st.session_state.last_maturity is not None and st.session_state.last_maturity != maturity):
    st.session_state.curves = []
st.session_state.curves.append((yields * 100, prices, f"{coupon_rate:.2f}% - {coupon_frequency} - {maturity:.1f}y"))
st.session_state.last_maturity = maturity

# Plot
fig, ax = plt.subplots()
for x_vals, y_vals, label in st.session_state.curves:
    ax.plot(x_vals, y_vals, label=label)

ax.set_title("Bond Price vs Yield to Maturity")
ax.set_xlabel("Yield to Maturity (%)")
ax.set_ylabel("Bond Price")
ax.grid(True)
ax.legend()

# Display the plot
st.pyplot(fig)
