import streamlit as st
import pandas as pd
import requests
import base64
from streamlit_extras.let_it_rain import rain

# Page Configuration
st.set_page_config(page_title="Film Wizard", page_icon="🎬", layout="wide")

# Initialize session state variables if they don't exist
if 'recommendations_df' not in st.session_state:
    st.session_state.recommendations_df = None

st.title("🎬 Film Wizard - Your Personal Movie Recommender")

# Sidebar for Upload
st.sidebar.header("Upload CSV for Recommendations")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])


BACKEND_URL = "https://film-wizard-backend-967675742185.europe-west1.run.app"
# BACKEND_URL = "http://127.0.0.1:8080"

# Load and display GIF
path_to_gif = "data/Wizard Buffer.gif"
with open(path_to_gif, "rb") as file:
    data_url = base64.b64encode(file.read()).decode("utf-8")

# Function to display falling popcorn animation
def example():
    rain(
        emoji="🍿",
        font_size=100,
        falling_speed=1,
        animation_length=3,
    )



dataframe = None
if uploaded_file is not None:
    try:
        # Load CSV file
        dataframe = pd.read_csv(uploaded_file).dropna()
        dataframe.columns = [col.lower() for col in dataframe.columns]  # Lowercase column names
        required_columns = ['title', 'rating', 'year']
        missing_columns = [col for col in required_columns if col not in dataframe.columns]

        if missing_columns:
            st.sidebar.warning(f"Missing columns: {', '.join(missing_columns)}. Please check your CSV.")
        else:
            st.sidebar.success("File loaded successfully!")
            st.subheader("Your Uploaded Movie Ratings:")
            st.dataframe(dataframe[['title', 'rating', 'year']], use_container_width=True)
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
        dataframe = None

# Recommendation Button
if st.button("Get Recommendations") and dataframe is not None:
    with st.spinner("Generating recommendations..."):
        gif_placeholder = st.empty()
        gif_placeholder.markdown(
            f'<div style="display: flex; justify-content: center;">'
            f'<img src="data:image/gif;base64,{data_url}" width="70%" alt="gif">'
            f'</div>',
            unsafe_allow_html=True,
        )
        try:
            response = requests.post(f"{BACKEND_URL}/movie_predictions", json=dataframe.to_dict(orient="records"))
            if response.status_code == 200:
                data = response.json()
                if "predictions" in data and data["predictions"]:
                    df_recommendations = pd.DataFrame(data["predictions"])
                    st.session_state.recommendations_df = df_recommendations

                    # Field mapping
                    field_mapping = {
                        'title': 'Title',
                        'estimated_rating': 'Estimated Rating',
                        'runtime': 'Duration (min)',
                        'genres': 'Genre',
                        'Cluster': 'Cluster'
                    }

                    # Rename columns
                    display_columns = {col: field_mapping[col] for col in df_recommendations.columns if col in field_mapping}
                    df_recommendations.rename(columns=display_columns, inplace=True)

                    # Display movie posters first
                    if "poster_url" in df_recommendations.columns:
                        st.subheader("🎭 Movie Recommendations:")
                        image_urls = df_recommendations.dropna(subset=['poster_url'])[['poster_url', 'Title', 'Duration (min)', 'Estimated Rating']]

                        cols = st.columns(5)  # Create 5 columns for the grid
                        for index, row in image_urls.iterrows():
                            with cols[index % 5]:
                                st.image(row['poster_url'], width=120)  # Display the image
                                st.markdown(
                                    f"<div style='text-align: left; padding-top: 0px; padding-bottom: 15px;'>"
                                    f"<b>{row['Title']}</b><br>"
                                    f"<span style='color:black;'>{int(row['Duration (min)'])} mins</span><br>"
                                    f"<b>Estimated Rating:</b> {row['Estimated Rating']}"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                    else:
                        st.warning("No poster images available.")

                    #Turn off gif
                    gif_placeholder.empty()

                    # Display recommendation table after images
                    st.subheader("Recommended Movies:")
                    display_columns = ['Title', 'Estimated Rating', 'Duration (min)', 'Genres', 'Cluster']
                    print(df_recommendations.columns)
                    st.dataframe(df_recommendations[display_columns], use_container_width=True)
                    st.info(f"Showing {len(df_recommendations)} recommendations.")

                    response = requests.post(f"{BACKEND_URL}/cluster_info", json=df_recommendations.to_dict(orient="records"))

                    if response.status_code == 200:
                        data = response.json()
                        if "info" in data:
                            st.subheader("Recommended Movie Clusters:")

                            # Convert API response to DataFrame
                            cluster_df = pd.DataFrame(data["info"])
                            # Count occurrences of each cluster in recommendations_df
                            if "Cluster" in df_recommendations.columns:
                                cluster_counts = df_recommendations["Cluster"].value_counts().reset_index()

                                # Merge counts with cluster_df
                                cluster_df = cluster_df.merge(cluster_counts, on="Cluster", how="left").fillna(0)
                                cluster_df.columns = ["Cluster Num", "Movies In Cluster", 'Sentiment Entropy Lvl','Top Genres', 'Words/Min', 'Years Education', 'Recommendations']

                            # Display editable table
                            #edited_cluster_df = st.data_editor(cluster_df, num_rows="dynamic")

                            # Sort by "Count" column in descending order
                            sorted_cluster_df = cluster_df.sort_values(by="Recommendations", ascending=False)

                            # Show the sorted DataFrame
                            st.dataframe(sorted_cluster_df)

                        else:
                            st.warning("No clusters found.")
                    else:
                        st.error("Error fetching clusters.")
                else:
                    st.warning("No recommendations found.")


                # Remove GIF and trigger popcorn animation
                # gif_placeholder.empty()
                example()
            else:
                st.error(f"Error from API: Status code {response.status_code}")
                if hasattr(response, 'text'):
                    st.error(f"Response: {response.text}")
        except Exception as e:
            st.error(f"Error processing recommendation request: {e}")
