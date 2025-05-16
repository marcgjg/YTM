import streamlit as st
import numpy as np
import plotly.graph_objects as go
import uuid
import pandas as pd


import psutil


st.set_page_config(
    page_title="Bond YTM Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Now you can use other Streamlit commands
memory = psutil.virtual_memory()
st.metric("Used Memory", f"{memory.used / (1024.0 ** 2):.2f} MB")





def get_colors():
    return ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# Custom header with logo/title
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">📈 Bond Price vs Yield to Maturity</h1>', unsafe_allow_html=True)

# Add a description
with st.expander("ℹ️ About this tool", expanded=False):
    st.markdown("""
    This tool can be used in two different ways:
    - It can help you visualize the negative or inverse relationship between the **Yield to Maturity (YTM)**  of a bond and its **Price**.
    - You can also use this tool to compare the **Interest Rate Risk** or **Duration** of i) bonds with the same coupon rate but different maturities or ii) bonds with the same maturity but different coupon rates.
    """)

if 'curves' not in st.session_state:
    st.session_state.curves = {}
    st.session_state.curve_colors = {}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Bond Parameters")
    face_value = st.slider("Face Value (€):", 100, 10000, 100, 100)
    coupon_rate = st.slider("Coupon Rate (%):", 0.0, 10.0, 2.0, 0.25)
    coupon_frequency = st.selectbox("Coupon Frequency:", ["Annual", "Semi-Annual"])
    maturity = st.slider("Maturity (Years):", 0.5, 30.0, 10.0, 0.5)
    min_ytm, max_ytm = st.slider("YTM Range (%):", 0.0, 20.0, (0.0, 15.0), 0.1)

    st.subheader("Chart Controls")
    col_add, col_reset = st.columns(2)
    with col_add:
        add_curve = st.button("➕ Add to Chart", use_container_width=True)
    with col_reset:
        reset_button = st.button("🔄 Reset Chart", use_container_width=True)

    resolution = st.select_slider("Chart Resolution:", ["Low", "Medium", "High", "Very High"], value="Medium")
    resolution_points = {"Low": 100, "Medium": 250, "High": 500, "Very High": 1000}
    num_points = resolution_points[resolution]

    if reset_button:
        st.session_state.curves = {}
        st.session_state.curve_colors = {}

    st.subheader("Current Bond Analysis")
    periods_per_year = 1 if coupon_frequency == "Annual" else 2
    n_periods = int(maturity * periods_per_year)
    coupon_payment = face_value * (coupon_rate / 100) / periods_per_year
    current_ytm = 5.0

    def calculate_bond_price(yield_rate):
        return sum([coupon_payment / (1 + yield_rate / periods_per_year) ** t for t in range(1, n_periods + 1)]) + \
               face_value / (1 + yield_rate / periods_per_year) ** n_periods

    def calculate_duration(yield_rate):
        pv_payments = [coupon_payment / (1 + yield_rate / periods_per_year) ** t for t in range(1, n_periods + 1)]
        pv_payments.append(face_value / (1 + yield_rate / periods_per_year) ** n_periods)
        weighted_times = [t * payment / periods_per_year for t, payment in enumerate(pv_payments, 1)]
        return sum(weighted_times) / sum(pv_payments)

    current_price = calculate_bond_price(current_ytm / 100)
    duration = calculate_duration(current_ytm / 100)

    st.metric("Coupon Payment", f"€{coupon_payment:.2f}")
    st.metric("Total Periods", f"{n_periods}")
    st.metric("Duration @ 5% YTM", f"{duration:.2f} years")

with col2:
    st.subheader("Bond Price vs Yield Curve")
    yields = np.linspace(min_ytm / 100, max_ytm / 100, num_points)
    prices = [calculate_bond_price(ytm) for ytm in yields]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=yields * 100,
        y=prices,
        mode='lines',
        name=f"Current ({coupon_rate:.2f}% - {coupon_frequency} - {maturity:.1f}y)",
        line=dict(color='#3b82f6', width=2, dash='dash')
    ))

    for curve_key, (x_vals, y_vals, label) in st.session_state.curves.items():
        color = st.session_state.curve_colors.get(curve_key, "#1f77b4")
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=label,
            line=dict(color=color, width=3)))

    fig.add_shape(type="line", x0=min_ytm, y0=face_value, x1=max_ytm, y1=face_value,
        line=dict(color="rgba(128, 128, 128, 0.5)", width=2, dash="dash"))

    fig.update_layout(
        title="Bond Price vs Yield to Maturity",
        xaxis_title="Yield to Maturity (%)",
        yaxis_title="Bond Price (€)",
        height=600,
        font=dict(size=16),
        margin=dict(l=80, r=80, t=80, b=120),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    if add_curve:
        curve_label = f"{coupon_rate:.2f}% - {coupon_frequency} - {maturity:.1f}y"
        curve_key = f"{uuid.uuid4().hex[:5]}"
        x_values = (yields * 100).tolist()
        y_values = prices
        st.session_state.curves[curve_key] = (x_values, y_values, curve_label)
        color_idx = len(st.session_state.curve_colors) % len(get_colors())
        st.session_state.curve_colors[curve_key] = get_colors()[color_idx]
        st.success(f"Added bond: {curve_label}")

    st.subheader("Bond Prices at Selected Yields")
    specific_yields = np.arange(0, 20.5, 0.5) / 100
    specific_prices = [calculate_bond_price(ytm) for ytm in specific_yields]
    price_data = pd.DataFrame({"Yield to Maturity (%)": specific_yields * 100, "Bond Price (€)": np.round(specific_prices, 2)})
    st.dataframe(price_data, use_container_width=True)

st.markdown('<div class="footer">Bond Price vs Yield to Maturity Calculator | For educational purposes</div>', unsafe_allow_html=True)
