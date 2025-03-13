import streamlit as st
import requests

st.set_page_config(page_title="Film Wizard", page_icon="https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg", layout="wide")

st.title("🎬 Film Wizard - Your Personal Movie Recommender")

st.image("https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg", width=100)

st.subheader("Enter your User ID for Movie Recommendation:")
user_id = st.text_input("User ID")

if st.button("Get Recommendations"):
    if user_id:
        FASTAPI_URL = "http://127.0.0.1:8000/recommend"
        response = requests.get(FASTAPI_URL, params={"user_id": user_id})

        if response.status_code == 200:
            data = response.json()
            if "recommendations" in data:
                st.subheader("Recommended Movies:")
                for rec in data["recommendations"]:
                    st.write(f"🎬 {rec['movie_id']} - Probability: {rec['probability_of_liking']:.2f}")
                    print(f"Recommended: {rec['movie_id']} - Probability: {rec['probability_of_liking']:.2f}")
            else:
                st.warning("No recommendations found for this user.")
        else:
            st.error("Error fetching recommendations.")
    else:
        st.warning("Please enter a valid User ID")
