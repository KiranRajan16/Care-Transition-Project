import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Styling
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# Data loading
df = pd.read_csv("data/HHS_data.csv")

# Data correction
df['Date'] = pd.to_datetime(df['Date'])
df['Children in HHS Care'] = df['Children in HHS Care'].str.replace(',', '').str.strip().astype(int)
df = df.fillna(0)

df.columns = df.columns.str.strip().str.replace(" ", "_")
df.rename(columns={
    "Children_apprehended_and_placed_in_CBP_custody*": "Inflows",
    "Children_in_CBP_custody": "CBP_Custody",
    "Children_transferred_out_of_CBP_custody": "Transfers",
    "Children_in_HHS_Care": "HHS_Custody",
    "Children_discharged_from_HHS_Care": "Discharged"
}, inplace=True)

# Metrics
df['Transfer_Efficiency'] = df['Transfers'] / df['CBP_Custody']
df['Discharge_Effectiveness'] = df['Discharged'] / df['HHS_Custody']
df['Throughput'] = df['Discharged'] / df['CBP_Custody']
df['Backlog'] = df['CBP_Custody'] - df['Discharged']
df['Stability'] = df['Discharge_Effectiveness'].rolling(7).std()

# Title
st.markdown('<p class="title">Care Transition Efficiency & Placement Outcome Analytics</p>', unsafe_allow_html=True)

# Filters
st.sidebar.header("⚙️ User Capabilities")

# Date Range Selection
start = st.sidebar.date_input("Start Date", df['Date'].min())
end = st.sidebar.date_input("End Date", df['Date'].max())

filtered_df = df[(df['Date'] >= pd.to_datetime(start)) &
                 (df['Date'] <= pd.to_datetime(end))]

# Ratio-based Metric Toggle
metric_option = st.sidebar.selectbox(
    "Select Metric",
    ["Transfer_Efficiency", "Discharge_Effectiveness"]
)

# Threshold Alert
threshold = st.sidebar.slider(
    "Set Threshold",
    0.0, 1.0, 0.5
)

# KPI Cards
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

def kpi_card(title, value, color_class):
    return f"""
    <div class="kpi-card {color_class}">
        <p class="kpi-title">{title}</p>
        <h2 class="kpi-value">{value}</h2>
    </div>
    """

col1.markdown(kpi_card("🚀 Transfer Efficiency",
                       round(filtered_df['Transfer_Efficiency'].mean(),2),
                       "kpi-green"), unsafe_allow_html=True)

col2.markdown(kpi_card("📦 Discharge Effectiveness",
                       round(filtered_df['Discharge_Effectiveness'].mean(),2),
                       "kpi-blue"), unsafe_allow_html=True)

col3.markdown(kpi_card("⚡ Throughput",
                       round(filtered_df['Throughput'].mean(),2),
                       "kpi-orange"), unsafe_allow_html=True)

col4.markdown(kpi_card("📊 Max Backlog",
                       int(filtered_df['Backlog'].max()),
                       "kpi-red"), unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Pipeline",
    "Efficiency",
    "Bottlenecks",
    "Trends"
])
def plot_chart(data, x, y, title, ylabel):
    fig, ax = plt.subplots(figsize=(14,6))
    sns.lineplot(x=data[x], y=data[y], ax=ax)

    ax.set_title(title, color="#A78BFA", fontsize=16)
    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

def plot_with_alert(data, x, y, title, ylabel, threshold, metric_option):
    fig, ax = plt.subplots(figsize=(14,6))

    # Main line
    sns.lineplot(x=data[x], y=data[y], ax=ax)

    # Alert points (based on selected metric)
    alert_points = data[data[metric_option] < threshold]
    ax.scatter(alert_points[x], alert_points[y],
               color='red', s=50, label='Alert')

    # Threshold line (for visual reference)
    ax.axhline(y=threshold, color='red', linestyle='--', label='Threshold')

    ax.set_title(title, color="#A78BFA", fontsize=16)
    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig, use_container_width=True)   
    
# Pipeline
with tab1:
    st.subheader("Care Pipeline Flow")

    plot_chart(filtered_df, 'Date', 'CBP_Custody',
               "CBP Custody Trend", "Number of Children")

    plot_chart(filtered_df, 'Date', 'HHS_Custody',
               "HHS Custody Trend", "Number of Children")

    plot_chart(filtered_df, 'Date', 'Discharged',
               "Discharged Trend", "Number of Children")

# Efficiency
with tab2:
   st.subheader("Efficiency Analysis")
   plot_chart(filtered_df, 'Date', metric_option,
               f"{metric_option} Trend", "Value")

# Bottlenecks
with tab3:
    st.subheader("Bottleneck Analysis")

    # Bottleneck
    plot_chart(
        filtered_df,
        x='Date',
        y='Backlog',
        title="Backlog Trend (Bottleneck)",
        ylabel="Backlog"
    )

    st.markdown("---")

    # Alerts plot 
    plot_with_alert(
        filtered_df,
        x='Date',
        y=metric_option,
        title=f"{metric_option} Alert Monitoring",
        ylabel=metric_option,
        threshold=threshold,
        metric_option=metric_option
    )

    # ✅ Alert Logic
    alerts = filtered_df[filtered_df[metric_option] < threshold]

    if not alerts.empty:
        st.error(f"⚠️ {len(alerts)} Alert Points Detected")
        st.write(alerts[['Date', metric_option]])
    else:
        st.success("✅ No Issues Detected")

# Trends
with tab4:
    fig, ax = plt.subplots(figsize=(14,6))
    sns.lineplot(x=filtered_df['Date'], y=filtered_df['Stability'], ax=ax)

    ax.set_title("Stability Trend", color = "#A78BFA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Variation")

    st.pyplot(fig, use_container_width=True)

# Summary
st.subheader("📌 Insights Summary")

st.write(f"""
- Selected Metric: {metric_option}
- Average Value: {round(filtered_df[metric_option].mean(),2)}
- Highest Backlog: {int(filtered_df['Backlog'].max())}
- System shows {'⚠️ bottleneck' if filtered_df['Backlog'].mean() > 0 else '✅ smooth flow'}
""")

# Raw Data
if st.checkbox("Show Raw Data"):
    st.write(df)