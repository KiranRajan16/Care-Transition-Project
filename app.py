import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------ GLOBAL STYLING ------------------
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

# ------------------ LOAD DATA ------------------
df = pd.read_csv("data/HHS_data.csv")

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

# ------------------ METRICS ------------------
df['Transfer_Efficiency'] = df['Transfers'] / df['CBP_Custody']
df['Discharge_Effectiveness'] = df['Discharged'] / df['HHS_Custody']
df['Throughput'] = df['Discharged'] / df['CBP_Custody']
df['Backlog'] = df['CBP_Custody'] - df['Discharged']
df['Stability'] = df['Discharge_Effectiveness'].rolling(7).std()

# ------------------ TITLE ------------------
st.markdown(
    '<p style="color:#C084FC; font-size:50px; font-weight:bold;">Care Transition Analytics Dashboard</p>',
    unsafe_allow_html=True
)

# ------------------ FILTER ------------------
start = st.date_input("Start Date", df['Date'].min())
end = st.date_input("End Date", df['Date'].max())

df = df[(df['Date'] >= pd.to_datetime(start)) &
        (df['Date'] <= pd.to_datetime(end))]

# ------------------ KPI CARDS ------------------
st.subheader("Key Performance Indicators")

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

col1.markdown(kpi_card("Transfer Efficiency", round(df['Transfer_Efficiency'].mean(),2), "#4CAF50"), unsafe_allow_html=True)
col2.markdown(kpi_card("Discharge Effectiveness", round(df['Discharge_Effectiveness'].mean(),2), "#2196F3"), unsafe_allow_html=True)
col3.markdown(kpi_card("Throughput", round(df['Throughput'].mean(),2), "#FF9800"), unsafe_allow_html=True)
col4.markdown(kpi_card("Max Backlog", int(df['Backlog'].max()), "#F44336"), unsafe_allow_html=True)

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Pipeline",
    "Efficiency",
    "Bottlenecks",
    "Trends"
])
# ------------------ TAB 1 ------------------
with tab1:
    st.subheader("Care Pipeline Flow")

    fig, ax = plt.subplots()
    sns.lineplot(data=df[['CBP_Custody','HHS_Custody','Discharged']], ax=ax)
    ax.set_title("Pipeline Movement", color="#A78BFA")
    ax.set_xlabel("Time")
    ax.set_ylabel("Number of Children")

    st.pyplot(fig)

# ------------------ TAB 2 ------------------
with tab2:
    st.subheader("Efficiency Analysis")

    metric = st.selectbox("Select Metric", 
                          ["Transfer_Efficiency", "Discharge_Effectiveness"])

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.lineplot(x=df['Date'], y=df[metric], ax=ax)
    ax.set_title(f"{metric} Trend", color="#A78BFA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Efficiency")

    st.pyplot(fig)

# ------------------ TAB 3 ------------------
with tab3:
    st.subheader("Backlog Detection")

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.lineplot(x=df['Date'], y=df['Backlog'], ax=ax)
    ax.set_title("Backlog Trend", color="#A78BFA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Backlog")

    st.pyplot(fig)

# ------------------ TAB 4 ------------------
with tab4:
    st.subheader("Outcome Stability")

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.lineplot(x=df['Date'], y=df['Stability'], ax=ax)
    ax.set_title("Stability Trend", color="#A78BFA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Variation")

    st.pyplot(fig)

# ------------------ SUMMARY ------------------
st.subheader("Insights Summary")

st.write(f"""
- Average Transfer Efficiency: {round(df['Transfer_Efficiency'].mean(),2)}
- Highest Backlog: {int(df['Backlog'].max())}
- System shows {'⚠️ bottleneck' if df['Backlog'].mean() > 0 else '✅ smooth flow'}
""")

# ------------------ RAW DATA ------------------
if st.checkbox("Show Raw Data"):
    st.write(df)