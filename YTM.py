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

# Custom CSS for better styling (matching the previous apps)
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
    .stSlider label {
        font-weight: 500;
        color: #334155;
    }
    .plot-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .info-box {
        background-color: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0px 5px 5px 0px;
    }
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        padding: 1rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
    }
    .metric-label {
        color: #64748B;
        font-size: 0.9rem;
    }
    .bond-display {
        padding: 0.5rem 1rem;
        background-color: #EFF6FF;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #1E40AF;
    }
</style>
""", unsafe_allow_html=True)

def get_colors():
    """Return a list of aesthetically pleasing colors for the chart."""
    return [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Yellow-green
        '#17becf',  # Teal
    ]

# Custom header with logo/title
st.markdown('<h1 class="main-header">📈 Bond Price vs Yield to Maturity</h1>', unsafe_allow_html=True)

# Add a description
with st.expander("ℹ️ About this tool", expanded=False):
    st.markdown("""
    This tool visualizes the relationship between **Bond Price** and **Yield to Maturity (YTM)**.
    
    - The bond price and yield have an inverse relationship
    - As yields increase, bond prices decrease (and vice versa)
    - You can compare multiple bonds with different parameters
    
    Add curves to compare how different coupon rates and maturities affect the price-yield relationship.
    """)

# Initialize session state to store curves and colors
if 'curves' not in st.session_state:
    st.session_state.curves = {}  # {curve_id: (yields, prices, label)}
    st.session_state.curve_colors = {}

# Create columns for inputs and plot
col1, col2 = st.columns([1, 2])

with col1:
    # Card for bond parameters
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Bond Parameters</div>', unsafe_allow_html=True)
    
    # Face value display - fixed at 100
    face_value = 100
    st.markdown(f"<div class='bond-display'>Face Value: €{face_value:.2f}</div>", unsafe_allow_html=True)
    
    # Coupon rate input (0% to 10% in increments of 0.25%)
    coupon_rate = st.slider(
        "Coupon Rate (%):", 
        min_value=0.0, 
        max_value=10.0, 
        value=2.0, 
        step=0.25,
        help="Annual interest rate paid by the bond"
    )
    
    # Coupon frequency (annual or semi-annual)
    coupon_frequency = st.selectbox(
        "Coupon Frequency:", 
        ["Annual", "Semi-Annual"],
        help="How often coupon payments are made"
    )
    
    # Remaining maturity input (0.5 to 30 years in 0.5-year steps)
    maturity = st.slider(
        "Maturity (Years):", 
        min_value=0.5, 
        max_value=30.0, 
        value=10.0, 
        step=0.5,
        help="Time until bond reaches maturity"
    )
    
    # YTM range visualization
    ytm_range = st.slider(
        "YTM Range (%):", 
        min_value=0.1, 
        max_value=20.0, 
        value=(0.1, 15.0), 
        step=0.1,
        help="Range of yields to show on chart"
    )
    min_ytm, max_ytm = ytm_range
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Card for chart controls
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Chart Controls</div>', unsafe_allow_html=True)
    
    col_add, col_reset = st.columns(2)
    with col_add:
        add_curve = st.button("➕ Add to Chart", use_container_width=True)
    with col_reset:
        reset_button = st.button("🔄 Reset Chart", use_container_width=True)
    
    resolution = st.select_slider(
        "Chart Resolution:",
        options=["Low", "Medium", "High", "Very High"],
        value="Medium",
        help="Number of data points calculated (higher is smoother but slower)"
    )
    
    resolution_points = {
        "Low": 100,
        "Medium": 250,
        "High": 500,
        "Very High": 1000
    }
    num_points = resolution_points[resolution]
    
    if reset_button:
        st.session_state.curves = {}
        st.session_state.curve_colors = {}
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Card for bond calculations
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Current Bond Analysis</div>', unsafe_allow_html=True)
    
    # Determine periods and coupon payment
    if coupon_frequency == "Annual":
        periods_per_year = 1
        frequency_text = "annually"
    else:
        periods_per_year = 2
        frequency_text = "semi-annually"
    
    n_periods = int(maturity * periods_per_year)
    coupon_payment = face_value * (coupon_rate / 100) / periods_per_year
    
    # Calculate current values for different metrics
    current_ytm = 5.0  # Example YTM of 5%
    
    # Calculate bond price at current YTM
    def calculate_bond_price(yield_rate):
        return sum([coupon_payment / (1 + yield_rate / periods_per_year) ** t for t in range(1, n_periods + 1)]) + \
               face_value / (1 + yield_rate / periods_per_year) ** n_periods
    
    current_price = calculate_bond_price(current_ytm / 100)
    
    # Calculate duration (simplified Macaulay duration)
    def calculate_duration(yield_rate):
        pv_payments = [coupon_payment / (1 + yield_rate / periods_per_year) ** t for t in range(1, n_periods + 1)]
        pv_payments.append(face_value / (1 + yield_rate / periods_per_year) ** n_periods)
        
        weighted_times = [t * payment / periods_per_year for t, payment in enumerate(pv_payments, 1)]
        return sum(weighted_times) / sum(pv_payments)
    
    duration = calculate_duration(current_ytm / 100)
    
    # Create three columns for the metrics
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">€{coupon_payment:.2f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-label">Coupon Payment ({frequency_text})</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_b:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{n_periods}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Periods</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_c:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{duration:.2f} years</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Duration @ 5% YTM</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Information box for bond pricing
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **Bond Price-Yield Relationship**
    
    - Higher coupon rates → Higher bond prices
    - Longer maturities → More price sensitivity to yield changes
    - Semi-annual coupons → More frequent compounding
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Calculate bond prices for current parameters
yields = np.linspace(min_ytm/100, max_ytm/100, num_points)
prices = []

for ytm in yields:
    price = calculate_bond_price(ytm)
    prices.append(price)

# Add curve to chart when button is clicked
if add_curve:
    curve_label = f"{coupon_rate:.2f}% - {coupon_frequency} - {maturity:.1f}y"
    curve_key = f"{uuid.uuid4().hex[:5]}"
    st.session_state.curves[curve_key] = (yields * 100, prices, curve_label)
    
    # Assign a color from our palette
    colors = get_colors()
    color_idx = len(st.session_state.curve_colors) % len(colors)
    st.session_state.curve_colors[curve_key] = colors[color_idx]
    
    # Show success message
    st.success(f"Added bond: {curve_label}")

with col2:
    # Card for the chart
    st.markdown('<div class="card plot-container">', unsafe_allow_html=True)
    
    # Create a plotly figure for better interactivity
    fig = go.Figure()
    
    # Add the current curve (dashed line if not saved)
    fig.add_trace(go.Scatter(
        x=yields * 100,
        y=prices,
        mode='lines',
        name=f"Current ({coupon_rate:.2f}% - {coupon_frequency} - {maturity:.1f}y)",
        line=dict(color='#3b82f6', width=2, dash='dash'),
        hovertemplate='YTM: %{x:.2f}%<br>Price: €%{y:.2f}<extra></extra>'
    ))
    
    # Add saved curves
    for curve_key, (x_vals, y_vals, label) in st.session_state.curves.items():
        color = st.session_state.curve_colors.get(curve_key, "#1f77b4")
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='lines',
            name=label,
            line=dict(color=color, width=3),
            hovertemplate='YTM: %{x:.2f}%<br>Price: €%{y:.2f}<extra></extra>'
        ))
    
    # Add a horizontal line at par value
    fig.add_shape(
        type="line",
        x0=min_ytm,
        y0=face_value,
        x1=max_ytm,
        y1=face_value,
        line=dict(
            color="rgba(128, 128, 128, 0.5)",
            width=2,
            dash="dash",
        )
    )
    
    # Add annotation for par value
    fig.add_annotation(
        x=min_ytm,
        y=face_value,
        text=f"Par Value: €{face_value}",
        showarrow=False,
        yshift=10,
        xshift=5,
        font=dict(color="rgba(128, 128, 128, 1)")
    )
    
    # Customize the layout
    fig.update_layout(
        title=dict(
            text="Bond Price vs Yield to Maturity",
            font=dict(size=24, family="Arial, sans-serif", color="#1E3A8A"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Yield to Maturity (%)",
            tickformat='.1f',
            gridcolor='rgba(230, 230, 230, 0.8)',
            range=[min_ytm, max_ytm]  # Explicitly set x-axis range
        ),
        yaxis=dict(
            title="Bond Price (€)",
            gridcolor='rgba(230, 230, 230, 0.8)',
            tickformat=',.2f',
        ),
        plot_bgcolor='rgba(248, 250, 252, 0.5)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=600,
        margin=dict(l=60, r=40, t=80, b=80)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Educational content
    with st.expander("📘 Understanding Bond Pricing", expanded=False):
        st.markdown("""
        ### The Bond Price Formula
        
        The price of a bond is the present value of all future cash flows:
        
        $Price = \sum_{t=1}^{n} \\frac{C}{(1+y)^t} + \\frac{F}{(1+y)^n}$
        
        Where:
        - $C$ = Coupon payment
        - $F$ = Face value
        - $y$ = Yield per period
        - $n$ = Number of periods
        
        ### Key Concepts
        
        **Par, Premium, and Discount:**
        - When price = face value, the bond trades at **par**
        - When price > face value, the bond trades at a **premium**
        - When price < face value, the bond trades at a **discount**
        
        **Duration:**
        Duration measures a bond's sensitivity to interest rate changes.
        Longer duration means higher price sensitivity to yield changes.
        
        **Bond Price-Yield Relationship:**
        - Bond prices and yields move in opposite directions
        - The relationship is non-linear (convex)
        - This property is known as "convexity"
        """)

# Footer
st.markdown('<div class="footer">Bond Price vs Yield to Maturity Calculator | For educational purposes</div>', unsafe_allow_html=True)
