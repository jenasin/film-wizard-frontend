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


#BACKEND_URL = "https://film-wizard-backend-967675742185.europe-west1.run.app"
BACKEND_URL = "http://127.0.0.1:8080"

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
        animation_length=2,
    )

dataframe = None
if uploaded_file is not None:
    try:
        # Load CSV file
        dataframe = pd.read_csv(uploaded_file).dropna()

        # Convert all column names to lowercase for consistency
        dataframe.columns = [col.lower() for col in dataframe.columns]

        # Ensure required columns exist
        required_columns = ['title', 'rating', 'year']
        missing_columns = [col for col in required_columns if col not in dataframe.columns]

        if missing_columns:
            st.sidebar.warning(f"Missing columns: {', '.join(missing_columns)}. Please check your CSV.")
        else:
            st.sidebar.success("File loaded successfully!")

            # Display input data
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
            f'''
            <div style="display: flex; justify-content: center;">
                <img src="data:image/gif;base64,{data_url}" width="70%" alt="gif">
            </div>
            ''',
            unsafe_allow_html=True,
        )

        try:
            # Send request to API
            response = requests.post(f"{BACKEND_URL}/movie_predictions", json=dataframe.to_dict(orient="records"))

            if response.status_code == 200:
                data = response.json()

                if "predictions" in data and data["predictions"]:
                    # Convert API response to DataFrame
                    df_recommendations = pd.DataFrame(data["predictions"])

                    # Store in session state
                    st.session_state.recommendations_df = df_recommendations

                    # Mapping API response fields to display fields
                    field_mapping = {
                        'title': 'Title',
                        'estimated_rating': 'Estimated Rating',
                        'estimated rating': 'Estimated Rating',
                        'prediction': 'Estimated Rating',
                        'Duration (min)': 'Duration (min)',
                        'runtime': 'Duration (min)',
                        'length': 'Duration (min)',
                        'genres': 'Genre',
                        'genre': 'Genre',
                        'Cluster': 'Cluster'
                    }

                    # Filter and rename columns
                    display_columns = []
                    rename_dict = {}

                    for api_col, display_name in field_mapping.items():
                        matching_cols = [col for col in df_recommendations.columns if col.lower() == api_col.lower()]
                        if matching_cols:
                            col = matching_cols[0]
                            display_columns.append(col)
                            rename_dict[col] = display_name

                    # Keep only the required columns in preferred order
                    preferred_order = ['Title', 'Estimated Rating', 'Duration (min)', 'Genre', 'Cluster']
                    display_columns = sorted(
                        display_columns,
                        key=lambda col: preferred_order.index(rename_dict[col]) if rename_dict[col] in preferred_order else len(preferred_order)
                    )

                    # Final DataFrame for display
                    if display_columns:
                        display_df = df_recommendations[display_columns].copy().rename(columns=rename_dict)
                    else:
                        display_df = df_recommendations.copy()

                    # Display recommendations
                    st.subheader("Recommended Movies:")
                    st.dataframe(display_df, use_container_width=True)

                    # Show number of recommendations
                    st.info(f"Showing {len(display_df)} recommendations.")

                    # Display movie posters if `poster_url` exists
                    if "poster_url" in df_recommendations.columns:
                        st.subheader("🎭 Movie Posters:")
                        image_urls = df_recommendations["poster_url"].dropna().tolist()

                        # Display images in a grid layout
                        cols = st.columns(5)  # Create 5 columns for the grid
                        for index, url in enumerate(image_urls):
                            with cols[index % 5]:  # Loop through columns
                                st.image(url, width=120)  # Display the image
                                st.write(df_recommendations.dropna(subset='poster_url').loc[index, 'Title'])
                                # st.write(df_recommendations.dropna(subset='poster_url').loc[index, 'Genre'])
                                st.write(df_recommendations.dropna(subset='poster_url').loc[index, 'Duration (min)'])
                                st.write(f"Estimated Rating: {df_recommendations.dropna(subset='poster_url').loc[index, 'Estimated Rating']}")
                    else:
                        st.warning("No poster images available.")
                    response = requests.post(f"{BACKEND_URL}/cluster_info", json=df_recommendations.to_dict(orient="records"))

                    ####
                    if response.status_code == 200:
                        data = response.json()
                        if "info" in data:
                            st.subheader("Recommended Movie Clusters:")
                            
                            # Convert API response to DataFrame
                            cluster_df = pd.DataFrame(data["info"])
                            # Count occurrences of each cluster in recommendations_df
                            if "Cluster" in recommendations_df.columns:
                                cluster_counts = recommendations_df["Cluster"].value_counts().reset_index()
                                
                                # Merge counts with cluster_df
                                cluster_df = cluster_df.merge(cluster_counts, on="Cluster", how="left").fillna(0)
                                cluster_df.columns = ["Cluster Num", "Movies In Cluster", 'Sentiment Entropy Lvl', 'Words/Min', 'Years Education', 'Recommendations']

                            # Display editable table
                            edited_cluster_df = st.data_editor(cluster_df, num_rows="dynamic")

                            # Sort by "Count" column in descending order
                            sorted_cluster_df = edited_cluster_df.sort_values(by="Count", ascending=False)

                            # Show the sorted DataFrame
                            st.dataframe(sorted_cluster_df)

                        else:
                            st.warning("No clusters found.")
                    else:
                        st.error("Error fetching clusters.")
                    ######
                else:
                    st.warning("No recommendations found.")

                # Remove GIF and trigger popcorn animation
                gif_placeholder.empty()
                example()
            else:
                st.error(f"Error from API: Status code {response.status_code}")
                if hasattr(response, 'text'):
                    st.error(f"Response: {response.text}")

        except Exception as e:
            st.error(f"Error processing recommendation request: {e}")
