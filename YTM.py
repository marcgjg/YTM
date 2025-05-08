import streamlit as st
import numpy as np
import plotly.graph_objects as go
import uuid
import pandas as pd

# Set the page layout to wide and add a custom title/icon
st.set_page_config(
    page_title="Bond YTM Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
        text-align: center;
    }
    .card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E2E8F0;
        font-size: 0.8rem;
        color: #64748B;
    }
</style>
""", unsafe_allow_html=True)

def get_colors():
    return ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

st.markdown('<h1 class="main-header">📈 Bond Price vs Yield to Maturity</h1>', unsafe_allow_html=True)

if 'curves' not in st.session_state:
    st.session_state.curves = {}
    st.session_state.curve_colors = {}

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Bond Parameters</div>', unsafe_allow_html=True)

    face_value = st.slider(
        "Face Value (€):",
        min_value=100,
        max_value=10000,
        value=100,
        step=100,
        help="The nominal value of the bond at maturity"
    )

    coupon_rate = st.slider("Coupon Rate (%):", 0.0, 10.0, 2.0, 0.25)
    coupon_frequency = st.selectbox("Coupon Frequency:", ["Annual", "Semi-Annual"])
    maturity = st.slider("Maturity (Years):", 0.5, 30.0, 10.0, 0.5)
    ytm_range = st.slider("YTM Range (%):", 0.1, 20.0, (0.1, 15.0), 0.1)
    min_ytm, max_ytm = ytm_range
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Chart Controls</div>', unsafe_allow_html=True)

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

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Current Bond Analysis</div>', unsafe_allow_html=True)

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
    st.markdown('</div>', unsafe_allow_html=True)

# Plotting logic
with col2:
    st.markdown('<div class="card plot-container">', unsafe_allow_html=True)
    yields = np.linspace(min_ytm / 100, max_ytm / 100, num_points)
    prices = [calculate_bond_price(ytm) for ytm in yields]

    fig = go.Figure()

    # Add the current curve (dashed line, not added to saved curves to avoid duplicate legend)
    fig.add_trace(go.Scatter(
        x=yields * 100,
        y=prices,
        mode='lines',
        name=f"Current ({coupon_rate:.2f}% - {coupon_frequency} - {maturity:.1f}y)",
        line=dict(color='#3b82f6', width=2, dash='dash'),
        showlegend=True  # Ensure only one legend for current bond
    ))

    for curve_key, (x_vals, y_vals, label) in st.session_state.curves.items():
        color = st.session_state.curve_colors.get(curve_key, "#1f77b4")
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=label,
            line=dict(color=color, width=3)))

    fig.add_shape(type="line", x0=min_ytm, y0=face_value, x1=max_ytm, y1=face_value,
        line=dict(color="rgba(128, 128, 128, 0.5)", width=2, dash="dash"))

    fig.update_layout(title="Bond Price vs Yield to Maturity",
        xaxis_title="Yield to Maturity (%)",
        yaxis_title="Bond Price (€)",
        height=600,
        font=dict(size=16),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))",
        yaxis_title="Bond Price (€)", height=600)

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

    st.markdown('</div>', unsafe_allow_html=True)

    specific_yields = np.arange(0, 20.5, 0.5) / 100
    specific_prices = [calculate_bond_price(ytm) for ytm in specific_yields]
    price_data = pd.DataFrame({"Yield to Maturity (%)": specific_yields * 100, "Bond Price (€)": np.round(specific_prices, 2)})
    st.dataframe(price_data, use_container_width=True)

st.markdown('<div class="footer">Bond Price vs Yield to Maturity Calculator | For educational purposes</div>', unsafe_allow_html=True)
