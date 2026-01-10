# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from databricks import sql


# CONFIGURATION

st.set_page_config(page_title="Canada Air Quality", layout="wide")

DATABRICKS_CONFIG = {
    "host": st.secrets["DATABRICKS_HOST"],
    "http_path": st.secrets["DATABRICKS_HTTP_PATH"],
    "token": st.secrets["DATABRICKS_TOKEN"]
}

POLLUTANTS = {
    "pm25": ("PM2.5", "Fine particles smaller than 2.5 micrometers. Can penetrate deep into lungs and bloodstream, causing respiratory and cardiovascular problems."),
    "pm10": ("PM10", "Coarse particles smaller than 10 micrometers. Can irritate eyes, nose, and throat. Aggravates asthma and breathing difficulties."),
    "o3": ("Ozone (O₃)", "Ground-level ozone formed by sunlight reacting with pollutants. Triggers chest pain, coughing, and worsens asthma."),
    "no2": ("Nitrogen Dioxide (NO₂)", "Produced by vehicle emissions and power plants. Irritates airways and contributes to smog and acid rain."),
    "so2": ("Sulfur Dioxide (SO₂)", "Released from burning fossil fuels. Causes breathing difficulties and contributes to acid rain."),
    "co": ("Carbon Monoxide (CO)", "Colorless, odorless gas from incomplete combustion. Reduces oxygen delivery in the body.")
}

MAP_CONFIG = {
    "zoom": 2.5,
    "center": {"lat": 55.0, "lon": -95.0},
    "style": "open-street-map",
    "height": 600,
    "marker_size": 12,
    "marker_opacity": 0.7,
    "color_scale": "RdYlGn_r"
}


# DATABASE FUNCTIONS

@st.cache_resource
def get_connection():
    return sql.connect(
        server_hostname=DATABRICKS_CONFIG["host"],
        http_path=DATABRICKS_CONFIG["http_path"],
        access_token=DATABRICKS_CONFIG["token"]
    )

def run_query(query):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)

@st.cache_data(ttl=300)
def get_available_dates():
    query = """
        SELECT DISTINCT date_id 
        FROM airquality.gold.fact_measurements 
        WHERE date_id IS NOT NULL
        ORDER BY date_id DESC
    """
    return run_query(query)["date_id"].tolist()

@st.cache_data(ttl=300)
def get_available_parameters():
    query = "SELECT DISTINCT parameter_name FROM airquality.gold.dim_parameters"
    return run_query(query)["parameter_name"].tolist()

@st.cache_data(ttl=300)
def get_measurements(parameter_name, selected_date):
    query = f"""
        SELECT 
            l.location_name,
            l.locality,
            l.latitude,
            l.longitude,
            p.parameter_units,
            f.datetime_utc,
            f.value,
            CONCAT(LPAD(HOUR(f.datetime_utc), 2, '0'), ':00') as time_window
        FROM airquality.gold.fact_measurements f
        JOIN airquality.gold.dim_locations l ON f.location_id = l.location_id
        JOIN airquality.gold.dim_parameters p ON f.parameter_id = p.parameter_id
        WHERE p.parameter_name = '{parameter_name}'
          AND f.date_id = '{selected_date}'
        ORDER BY f.datetime_utc
    """
    return run_query(query)


# UI COMPONENTS

def render_sidebar(available_pollutants, available_dates):
    st.sidebar.header("Filters")
    
    # Date selector (first)
    selected_date = st.sidebar.selectbox("Select Date", available_dates, index=0)
    
    # Pollutant selector (second)
    options = list(available_pollutants.keys())
    labels = [available_pollutants[p][0] for p in options]
    idx = st.sidebar.selectbox("Select Pollutant", range(len(options)), format_func=lambda i: labels[i])
    selected_param = options[idx]
    
    # Description in sidebar
    name, description = available_pollutants[selected_param]
    st.sidebar.info(f"**{name}**: {description}")
    
    return selected_param, selected_date

def render_metrics(df, units):
    col1, col2, col3 = st.columns(3)
    col1.metric("Lowest", f"{df['value'].min():.3f} {units}")
    col2.metric("Median", f"{df['value'].median():.3f} {units}")
    col3.metric("Highest", f"{df['value'].max():.3f} {units}")

def render_map(df, units):
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        color="value",
        hover_name="location_name",
        hover_data={"locality": True, "value": ":.3f", "datetime_utc": True, "parameter_units": True, "latitude": False, "longitude": False, "time_window": False},
        color_continuous_scale=MAP_CONFIG["color_scale"],
        zoom=MAP_CONFIG["zoom"],
        center=MAP_CONFIG["center"],
        mapbox_style=MAP_CONFIG["style"],
        animation_frame="time_window"
    )
    fig.update_traces(marker=dict(size=MAP_CONFIG["marker_size"], opacity=MAP_CONFIG["marker_opacity"]))
    fig.update_layout(height=MAP_CONFIG["height"], coloraxis_colorbar=dict(title=units))
    st.plotly_chart(fig, use_container_width=True)


# MAIN APP

def main():
    st.title("Canada Air Quality Dashboard")
    
    try:
        with st.spinner("Connecting to Databricks..."):
            available_dates = get_available_dates()
            db_parameters = get_available_parameters()
        
        # Filter to available pollutants
        available_pollutants = {k: v for k, v in POLLUTANTS.items() if k in db_parameters}
        
        # Sidebar
        selected_param, selected_date = render_sidebar(available_pollutants, available_dates)
        
        # Load data
        name = available_pollutants[selected_param][0]
        with st.spinner(f"Loading {name} data..."):
            df = get_measurements(selected_param, selected_date)
        
        if df.empty:
            st.warning(f"No data found for {name} on {selected_date}.")
            return
        
        units = df["parameter_units"].iloc[0]
        
        # Summary
        st.markdown(f"**Date**: {selected_date} | **Stations**: {df['location_name'].nunique()} | **Readings**: {len(df)}")
        
        # Render Statistics
        render_metrics(df, units)

        # Render Map
        render_map(df, units)
        
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Make sure the SQL Warehouse is running and your credentials are correct.")

if __name__ == "__main__":
    main()