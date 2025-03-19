import streamlit as st
import pandas as pd
import requests
import time
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



# """### gif from local file"""
path_to_gif = "data/Wizard Buffer.gif"
file_ = open(path_to_gif, "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

#code to display gif
# st.markdown(
#     f'<img src="data:image/gif;base64,{data_url}" alt="gif">',
#     unsafe_allow_html=True,
# )

def example():
    rain(
        emoji="🍿",
        font_size=100,
        falling_speed=1,
        animation_length=2,
    )

# example()

dataframe = None
if uploaded_file is not None:
    try:
        # Load the CSV
        dataframe = pd.read_csv(uploaded_file).dropna()

        # Convert all column names to lowercase for consistency
        dataframe.columns = [col.lower() for col in dataframe.columns]

        # Check if required columns exist
        required_columns = ['title', 'year', 'rating']
        missing_columns = [col for col in required_columns if col not in dataframe.columns]

        if missing_columns:
            st.sidebar.warning(f"Missing columns: {', '.join(missing_columns)}. Please make sure your CSV has this data.")
        else:
            st.sidebar.success("File loaded successfully!")

            # Display input data with appropriate columns
            st.subheader("Your Movie Ratings:")

            # Select and order columns for display
            display_columns = [col for col in ['title', 'rating', 'year'] if col in dataframe.columns]

            # Create a styled table display
            st.markdown("""
            <style>
            .styled-table {
                width: 100%;
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 14px;
                font-family: sans-serif;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
            }
            .styled-table thead tr {
                background-color: #1E88E5;
                color: white;
                text-align: left;
            }
            .styled-table th,
            .styled-table td {
                padding: 12px 15px;
                max-width: 200px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .styled-table tbody tr {
                border-bottom: 1px solid #dddddd;
            }
            .styled-table tbody tr:nth-of-type(even) {
                background-color: #f3f3f3;
            }
            .styled-table tbody tr:last-of-type {
                border-bottom: 2px solid #1E88E5;
            }
            </style>
            """, unsafe_allow_html=True)

            # Use Streamlit's dataframe with reduced width
            st.dataframe(
                dataframe[display_columns],
                use_container_width=True,
                column_config={
                    "title": st.column_config.TextColumn("Title", width="large"),
                    "rating": st.column_config.NumberColumn("Rating", format="%.1f", width="small"),
                    "year": st.column_config.NumberColumn("Year", width="small")
                }
            )

    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
        dataframe = None

# Recommendation Button
if st.button("Get Recommendations") and dataframe is not None:


    with st.spinner("Generating recommendations..."):
        # Display loading message and gif image
        wiz_gif = st.empty()
        wiz_gif.markdown(
        f'''
             <div style="display: flex; justify-content: center;">

            <img src="data:image/gif;base64,{data_url}" width = "70%" alt="gif">
            </div>
        ''',
        unsafe_allow_html=True,
        )
        try:
            # Send the data to the backend API
            response = requests.post(f"{BACKEND_URL}/movie_predictions", json=dataframe.to_dict(orient="records"))

            if response.status_code == 200:
                data = response.json()

                if "predictions" in data and data["predictions"]:
                    # Convert to DataFrame
                    df_recommendations = pd.DataFrame(data["predictions"])

                    # Store in session state
                    st.session_state.recommendations_df = df_recommendations

                    # Map API response fields to display fields (case-insensitive)
                    field_mapping = {
                        'title': 'Title',
                        'estimated_rating': 'Estimated Rating',
                        'estimated rating': 'Estimated Rating',
                        'prediction': 'Estimated Rating',
                        'year': 'Year',
                        'genres': 'Genre',
                        'genre': 'Genre'
                    }

                    # Clean column names and ensure they exist
                    display_columns = []
                    rename_dict = {}

                    # Process each column we want to display
                    for api_col, display_name in field_mapping.items():
                        # Find if this column exists in our data (case insensitive)
                        matching_cols = [col for col in df_recommendations.columns
                                       if col.lower() == api_col.lower()]

                        if matching_cols:
                            # Use the first matching column
                            col = matching_cols[0]
                            display_columns.append(col)
                            rename_dict[col] = display_name

                    # Always prioritize displaying title first, then rating, year, genre
                    preferred_order = ['Title', 'Estimated Rating', 'Year', 'Genre']

                    # Sort display_columns based on preferred order
                    display_columns = sorted(
                        display_columns,
                        key=lambda col: preferred_order.index(rename_dict[col])
                        if rename_dict[col] in preferred_order else len(preferred_order)
                    )

                    # Create display DataFrame with proper column order
                    if display_columns:
                        display_df = df_recommendations[display_columns].copy()
                        display_df = display_df.rename(columns=rename_dict)
                    else:
                        display_df = df_recommendations.copy()

                    # Extract available years and genres for filtering
                    years = []
                    genres = []

                    # Extract years if available
                    if 'Year' in display_df.columns:
                        years = sorted(display_df['Year'].dropna().unique(), reverse=True)

                    # Extract genres if available
                    if 'Genre' in display_df.columns:
                        all_genres = []
                        for genre_list in display_df['Genre'].dropna():
                            if isinstance(genre_list, str):
                                all_genres.extend([g.strip() for g in genre_list.split('|')])
                        genres = sorted(set(all_genres))

                    # Display Recommendations with styling
                    st.subheader("Recommended Movies:")

                    # Create interactive filters only if we have data
                    filtering_available = (len(years) > 0 or len(genres) > 0)

                    if filtering_available:
                        col1, col2 = st.columns(2)

                        with col1:
                            filter_year = st.selectbox(
                                "Filter by Year",
                                ["All"] + [str(y) for y in years] if years else ["All"]
                            )

                        with col2:
                            filter_genre = st.selectbox(
                                "Filter by Genre",
                                ["All"] + genres if genres else ["All"]
                            )

                        # Apply filters
                        filtered_df = display_df.copy()

                        if filter_year != "All" and 'Year' in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df['Year'] == int(filter_year)]

                        if filter_genre != "All" and 'Genre' in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df['Genre'].str.contains(filter_genre, case=False, na=False)]
                    else:
                        filtered_df = display_df.copy()

                    # Display with appropriate columns and formatting
                    column_config = {}

                    if 'Title' in filtered_df.columns:
                        column_config["Title"] = st.column_config.TextColumn("Title", width="large")

                    if 'Estimated Rating' in filtered_df.columns:
                        column_config["Estimated Rating"] = st.column_config.NumberColumn(
                            "Estimated Rating",
                            format="%.1f",
                            width="small"
                        )

                    if 'Year' in filtered_df.columns:
                        column_config["Year"] = st.column_config.NumberColumn("Year", width="small")

                    if 'Genre' in filtered_df.columns:
                        column_config["Genre"] = st.column_config.TextColumn("Genre", width="medium")

                    st.dataframe(
                        filtered_df,
                        use_container_width=True,
                        column_config=column_config
                    )

                    # Show number of recommendations
                    st.info(f"Showing {len(filtered_df)} recommendations out of {len(display_df)} total")
                    wiz_gif.empty()

                    example()
                else:
                    st.warning("No recommendations found in the API response.")
            else:
                st.error(f"Error from API: Status code {response.status_code}")
                if hasattr(response, 'text'):
                    st.error(f"Response: {response.text}")
        except Exception as e:
            st.error(f"Error processing recommendation request: {e}")
            import traceback
            st.error(traceback.format_exc())
