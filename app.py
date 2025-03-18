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
