import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Styling
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}

/* Title */
.title {
    color: #C084FC;
    font-size: 36px;
    font-weight: bold;
}

/* Subheaders */
h2, h3 {
    color: #A78BFA;
    font-family: 'Segoe UI', sans-serif;
}

/* General text */
p {
    font-size: 14px;
    color: #CCCCCC;
}
</style>
""", unsafe_allow_html=True)

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
st.markdown(
    '<p style="color:#C084FC; font-size:50px; font-weight:bold;">Care Transition Analytics Dashboard</p>',
    unsafe_allow_html=True
)
st.markdown("""
<style>

/* Sidebar background */
section[data-testid="stSidebar"] {
    background-color: #1E1E1E;
}

/* Sidebar header text */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FA1606;  /* 👈 Light purple */
    font-family: 'Segoe UI', sans-serif;
}

</style>
""", unsafe_allow_html=True)

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

def kpi_card(title, value, color):
    return f"""
    <div style="
        background-color:#1E1E1E;
        padding:20px;
        border-radius:12px;
        border-left:6px solid {color};
        font-family:'Segoe UI', sans-serif;
    ">
        <p style="color:#BBBBBB; font-size:14px;">{title}</p>
        <h2 style="color:white; font-size:28px;">{value}</h2>
    </div>
    """

col1.markdown(kpi_card("🚀 Transfer Efficiency",
                       round(filtered_df['Transfer_Efficiency'].mean(),2),
                       "#4CAF50"), unsafe_allow_html=True)

col2.markdown(kpi_card("📦 Discharge Effectiveness",
                       round(filtered_df['Discharge_Effectiveness'].mean(),2),
                       "#2196F3"), unsafe_allow_html=True)

col3.markdown(kpi_card("⚡ Throughput",
                       round(filtered_df['Throughput'].mean(),2),
                       "#FF9800"), unsafe_allow_html=True)

col4.markdown(kpi_card("📊 Max Backlog",
                       int(filtered_df['Backlog'].max()),
                       "#D31608"), unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Pipeline",
    "Efficiency",
    "Bottlenecks",
    "Trends"
])

# Pipeline
with tab1:
    fig, ax = plt.subplots(figsize=(14,6))
    sns.lineplot(data=filtered_df[['CBP_Custody','HHS_Custody','Discharged']], ax=ax)

    ax.set_title("Pipeline Movement", color="#A78BFA")
    ax.set_xlabel("Time")
    ax.set_ylabel("Number of Children")

    st.pyplot(fig, use_container_width=True)

# Efficiency
with tab2:
    fig, ax = plt.subplots(figsize=(14,6))
    sns.lineplot(x=filtered_df['Date'], y=filtered_df[metric_option], ax=ax)

    ax.set_title(f"{metric_option} Trend", color="#A78BFA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")

    st.pyplot(fig, use_container_width=True)

# Bottlenecks
with tab3:
    fig, ax = plt.subplots(figsize=(14,6))
    sns.lineplot(x=filtered_df['Date'], y=filtered_df['Backlog'], ax=ax)

    ax.set_title("Backlog Trend", color="#A78BFA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Backlog")

    st.pyplot(fig, use_container_width=True)

    # Alert Logic
    alerts = filtered_df[filtered_df[metric_option] < threshold]

    if not alerts.empty:
        st.error("⚠️ Alert: Threshold Breach Detected")
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

# Highlight alert points in red
alert_points = filtered_df[filtered_df[metric_option] < threshold]

fig, ax = plt.subplots(figsize=(14,6))
sns.lineplot(x=filtered_df['Date'], y=filtered_df[metric_option], ax=ax)

# highlight points
ax.scatter(alert_points['Date'], alert_points[metric_option], color='red', label='Alert')

ax.axhline(y=threshold, color='red', linestyle='--', label='Threshold')

ax.legend()

st.pyplot(fig)

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