import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Film Wizard", page_icon="https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg", layout="wide")

st.title("🎬 Film Wizard - Your Personal Movie Recommender")

st.image("https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg", width=100)

st.subheader("Upload CSV file for recommendations:")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
BACKEND_URL = "https://film-wizard-backend-967675742185.europe-west1.run.app"  # Ensure this matches your backend URL

dataframe = None
df_recommendations = None
cluster_df = None

if uploaded_file is not None:
    with st.spinner("Loading file..."):
        dataframe = pd.read_csv(uploaded_file).dropna()  # Read CSV and remove empty rows
        st.success("File loaded successfully!")

        st.subheader("Uploaded File Preview:")
        st.dataframe(dataframe)  # Display the cleaned dataframe

if st.button("Get Recommendations") and dataframe is not None:
    with st.spinner("Fetching recommendations..."):
        time.sleep(2)  # Simulate loading time

        # Convert DataFrame to JSON and send it to the backend
        response = requests.post(f"{BACKEND_URL}/movie_predictions", json=dataframe.to_dict(orient="records"))

        if response.status_code == 200:
            data = response.json()
            if "predictions" in data:
                st.subheader("Recommended Movies:")
                df_recommendations = pd.DataFrame(data["predictions"])
                st.dataframe(df_recommendations)  # Display as DataFrame
            else:
                st.warning("No recommendations found.")
        else:
            st.error("Error fetching recommendations.")

if st.button("Get Cluster Info") and df_recommendations is not None:
    with st.spinner("Fetching movie clusters..."):
        time.sleep(2)  # Simulate loading time
        
        BACKEND_URL = 'http://localhost:8501'
        # Convert DataFrame to JSON and send it to the backend
        response = requests.post(f"{BACKEND_URL}/cluster_info", json=df_recommendations.to_dict(orient="records"))

        if response.status_code == 200:
            data = response.json()
            if "info" in data:
                st.subheader("Recommended Movie Clusters:")
                cluster_df = pd.DataFrame(data["info"])
                st.dataframe(cluster_df)  # Display as DataFrame
            else:
                st.warning("No clusters found.")
        else:
            st.error("Error fetching clusters.")