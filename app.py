import streamlit as st
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os
import plotly.express as px

# Establish PostgreSQL connection

def get_engine():
    db_username = os.getenv('DB_SERVICE_USER')
    db_hostname = os.getenv('DB_HOST')
    db_port = "5432"
    database_name = "template1"
    db_password = os.getenv('DB_SERVICE_USER_PASSWORD')
    encoded_password = quote_plus(db_password)

    return create_engine(f'postgresql+psycopg2://{db_username}:{encoded_password}@{db_hostname}:{db_port}/{database_name}')

# Fetch users from the database
def fetch_users(engine):
    query = "SELECT DISTINCT \"user\" FROM tm_daily_checkin;"  # Adjust table/column name
    with engine.connect() as conn:
        result = conn.execute(text(query)).mappings()
        return [row['user'] for row in result]

# Fetch rows based on selected user
def fetch_user_data(engine, user_name):
    query = text("SELECT * FROM tm_daily_checkin WHERE \"user\" = :user_name")
    with engine.connect() as conn:
        result = conn.execute(query, {"user_name": user_name})
        return pd.DataFrame(result.fetchall(), columns=result.keys())   
    
# Fetch hours worked by project
def fetch_hours_by_project(engine):
    query = "SELECT project, SUM(hours) as total_hours FROM tm_daily_checkin GROUP BY project;"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# Fetch hours worked by employee
def fetch_hours_by_employee(engine):
    query = "SELECT \"user\", SUM(hours) as total_hours FROM tm_daily_checkin GROUP BY \"user\";"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

        # Fetch hours worked per month
def fetch_hours_by_month(engine):
    query = """
        SELECT 
            DATE_TRUNC('month', \"timestamp\") AS month, 
            SUM(hours) as total_hours 
        FROM 
            tm_daily_checkin 
        GROUP BY 
            month 
        ORDER BY 
            month;
        """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

st.title("✨ Hello! Select the user that you want to view in the dropdown below ✨")

load_dotenv()

engine = get_engine()
# Dropdown to select user
users = fetch_users(engine)
selected_user = st.selectbox("Select a user", users)

if selected_user:
    st.write(f"Showing data for: **{selected_user}**")
    user_data = fetch_user_data(engine, selected_user)
    user_data.drop(columns=['load_date_performed'], inplace=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.write(user_data)

    with col2:
        st.write(f"Hours per project by {selected_user}")
        grouped_project = user_data.groupby("project")["hours"].sum()
        st.bar_chart(grouped_project)

st.title("Want to see more general data? Check out the charts below! Check one of the boxes in the sidebar to see more 📊")
# Sidebar toggle for additional charts
st.sidebar.title("Overall Charts")
show_project_hours_chart = st.sidebar.checkbox("Show Total Hours Per Project")
show_employee_hours_chart = st.sidebar.checkbox("Show Total Hours Per Employee")
if show_project_hours_chart:
    # Bar chart for hours worked per project
    px.defaults.color_continuous_scale = px.colors.sequential.Plasma
    st.subheader("Total Hours Worked Per Project")
    project_hours = fetch_hours_by_project(engine)
    if not project_hours.empty:
        project_chart = px.bar(
            project_hours,
            x="project",
            y="total_hours",
            title="Total Hours Worked Per Project",
            labels={"project": "Project", "total_hours": "Total Hours Worked"},
            )
        st.plotly_chart(project_chart)

if show_employee_hours_chart:
    # Bar chart for hours worked per employee
    st.subheader("Total Hours Worked Per Employee")
    employee_hours = fetch_hours_by_employee(engine)
    if not employee_hours.empty:
        employee_chart = px.bar(
            employee_hours,
            x="user",
            y="total_hours",
            title="Total Hours Worked Per Employee",
            labels={"user": "Employee", "total_hours": "Total Hours Worked"},
        )
        st.plotly_chart(employee_chart)

show_monthly_hours_chart = st.sidebar.checkbox("Show Total Hours Per Month")
if show_monthly_hours_chart:
    # Line chart for hours worked per month
    st.subheader("Total Hours Worked Per Month")
    monthly_hours = fetch_hours_by_month(engine)
    if not monthly_hours.empty:
        monthly_chart = px.line(
            monthly_hours,
            x="month",
            y="total_hours",
            title="Total Hours Worked Per Month",
            labels={"month": "Month", "total_hours": "Total Hours Worked"},
        )
        st.plotly_chart(monthly_chart)
        # Footer
st.markdown("---")
st.markdown("**by Carlo Catayna**")
st.markdown("carlocatayna13@gmail.com")