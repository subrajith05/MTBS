import streamlit as st
import datetime
import streamlit_extras.switch_page_button as spb
from db_utils import execute_query, execute_update

def check_authentication():
    # Check if user is logged in and is an admin
    if 'logged_in' not in st.session_state or not st.session_state['logged_in'] or 'is_admin' not in st.session_state or not st.session_state['is_admin']:
        st.error("Unauthorized access. Please login as admin.")
        st.stop()

def main():
    st.set_page_config(page_title="Admin Panel", layout="wide", initial_sidebar_state="collapsed")
    
    # Verify admin authentication
    check_authentication()

    st.title("🎬 Admin Panel")

    # Sidebar menu
    menu = st.radio("Select an option:", ["Add Movie", "Remove Movie", "Adjust Shows", "Movie List"])

    if menu == "Add Movie":
        st.subheader("➕ Add a New Movie")
        
        # Get the customer_id associated with admin for attribution
        admin_id = st.session_state.get('admin_id')
        
        # Get website ID
        web_id_query = "SELECT web_id FROM website LIMIT 1"
        web_results = execute_query(web_id_query)
        
        if web_results:
            web_id = web_results[0]['web_id']
            
            movie_title = st.text_input("Movie Title")
            movie_desc = st.text_area("Movie Description")
            release_date = st.date_input("Release Date")
            screen_till = st.date_input("Last screening date")
            poster_url = st.text_input("Movie Poster URL")
            
            # Get available screens
            screens_query = "SELECT screen_id, screen_name FROM screen"
            screens = execute_query(screens_query)
            
            if screens:
                screen_options = {screen['screen_name']: screen['screen_id'] for screen in screens}
                selected_screen = st.selectbox("Select Screen", list(screen_options.keys()))
                screen_id = screen_options[selected_screen]
                
                # Show time inputs
                st.subheader("Show Times")
                
                show_times = []
                for i in range(3):  # Allow adding up to 3 show times
                    show_time = st.time_input(f"Show Time {i+1}", datetime.time(10 + i*3, 0))
                    if st.checkbox(f"Include Show Time {i+1}", value=True):
                        show_times.append(show_time)
                
                submit = st.button("Add Movie")
                
                if submit and movie_title and movie_desc and show_times:
                    # Insert movie data
                    movie_query = """
                    INSERT INTO movie (movie_title, movie_description, poster_url, customer_id, web_id) 
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    movie_result = execute_update(movie_query, (movie_title, movie_desc, poster_url, admin_id, web_id))
                    
                    if movie_result > 0:
                        # Get the newly inserted movie ID
                        movie_id_query = "SELECT LAST_INSERT_ID() as movie_id"
                        movie_id_result = execute_query(movie_id_query)
                        
                        if movie_id_result:
                            movie_id = movie_id_result[0]['movie_id']
                            
                            # Link movie to screen
                            screen_link_query = """
                            INSERT INTO movie_played_on_screen (movie_id, screen_id) 
                            VALUES (%s, %s)
                            """
                            execute_update(screen_link_query, (movie_id, screen_id))
                            

                            # Add schedules
                            for show_time in show_times:
                                schedule_query = """
                                INSERT INTO schedule (show_time, show_date, movie_id) 
                                VALUES (%s, %s, %s)
                                """
                                execute_update(schedule_query, (show_time, release_date, movie_id))
                                
                                # Add to movie_played_on_schedule
                                movie_schedule_query = """
                                INSERT INTO movie_played_on_schedule (show_time, movie_id) 
                                VALUES (%s, %s)
                                """
                                execute_update(movie_schedule_query, (show_time, movie_id))
                            
                            st.success(f"Movie '{movie_title}' added successfully!")
                        else:
                            st.error("Failed to retrieve movie ID.")
                    else:
                        st.error("Failed to add movie.")
            else:
                st.error("No screens available. Please add screens first.")
        else:
            st.error("Website information not found.")

    elif menu == "Remove Movie":
        st.subheader("🗑️ Remove a Movie")
        
        # Get list of movies
        movies_query = "SELECT movie_id, movie_title FROM movie"
        movies = execute_query(movies_query)
        
        if movies:
            # Display movies with their IDs
            st.write("Current Movies:")
            for movie in movies:
                st.write(f"ID: {movie['movie_id']} - Title: {movie['movie_title']}")
            
            movie_to_remove = st.number_input("Enter Movie ID to Remove", min_value=1, step=1)
            
            remove = st.button("Remove Movie")
            
            if remove:
                # First check if the movie exists
                check_query = "SELECT movie_title FROM movie WHERE movie_id = %s"
                movie_check = execute_query(check_query, (movie_to_remove,))
                
                if movie_check:
                    movie_title = movie_check[0]['movie_title']
                    
                    # Delete from dependent tables first
                    execute_update("DELETE FROM movie_played_on_schedule WHERE movie_id = %s", (movie_to_remove,))
                    execute_update("DELETE FROM schedule WHERE movie_id = %s", (movie_to_remove,))
                    execute_update("DELETE FROM movie_played_on_screen WHERE movie_id = %s", (movie_to_remove,))
                    
                    # Now delete the movie
                    movie_delete = execute_update("DELETE FROM movie WHERE movie_id = %s", (movie_to_remove,))
                    
                    if movie_delete > 0:
                        st.warning(f"Movie '{movie_title}' (ID: {movie_to_remove}) removed successfully!")
                    else:
                        st.error("Failed to remove movie.")
                else:
                    st.error(f"No movie found with ID {movie_to_remove}")
        else:
            st.info("No movies available in the database.")

    elif menu == "Adjust Shows":
        st.subheader("🎭 Adjust Movie Shows")
        
        # Get list of movies
        movies_query = "SELECT movie_id, movie_title FROM movie"
        movies = execute_query(movies_query)
        
        if movies:
            movie_options = {movie['movie_title']: movie['movie_id'] for movie in movies}
            selected_movie = st.selectbox("Select Movie", list(movie_options.keys()))
            movie_id = movie_options[selected_movie]
            
            # Get current show times for this movie
            shows_query = """
            SELECT schedule_id, show_time, show_date 
            FROM schedule 
            WHERE movie_id = %s
            """
            shows = execute_query(shows_query, (movie_id,))
            
            if shows:
                st.write("Current Show Times:")
                for show in shows:
                    st.write(f"ID: {show['schedule_id']} - Date: {show['show_date']} - Time: {show['show_time']}")
                
                # Allow updating a specific show
                schedule_id = st.number_input("Enter Schedule ID to update", min_value=1, step=1)
                new_time = st.time_input("Select New Show Time")
                new_date = st.date_input("Select New Show Date")
                
                update = st.button("Update Show")
                
                if update:
                    # Check if schedule exists
                    check_query = "SELECT schedule_id FROM schedule WHERE schedule_id = %s"
                    schedule_check = execute_query(check_query, (schedule_id,))
                    
                    if schedule_check:
                        # Update the schedule
                        update_query = """
                        UPDATE schedule 
                        SET show_time = %s, show_date = %s 
                        WHERE schedule_id = %s
                        """
                        schedule_update = execute_update(update_query, (new_time, new_date, schedule_id))
                        
                        if schedule_update > 0:
                            # Also update movie_played_on_schedule if necessary
                            execute_update("""
                            UPDATE movie_played_on_schedule 
                            SET show_time = %s 
                            WHERE movie_id = %s
                            """, (new_time, movie_id))
                            
                            st.info(f"Show for '{selected_movie}' updated to {new_time} on {new_date}")
                        else:
                            st.error("Failed to update show.")
                    else:
                        st.error(f"No schedule found with ID {schedule_id}")
            else:
                st.info(f"No show times scheduled for '{selected_movie}'")
                
                # Option to add a new show time
                st.subheader("Add New Show Time")
                new_time = st.time_input("New Show Time")
                new_date = st.date_input("New Show Date")
                
                add_show = st.button("Add Show")
                
                if add_show:
                    # Add new schedule
                    schedule_query = """
                    INSERT INTO schedule (show_time, show_date, movie_id) 
                    VALUES (%s, %s, %s)
                    """
                    schedule_add = execute_update(schedule_query, (new_time, new_date, movie_id))
                    
                    if schedule_add > 0:
                        # Add to movie_played_on_schedule
                        execute_update("""
                        INSERT INTO movie_played_on_schedule (show_time, movie_id) 
                        VALUES (%s, %s)
                        """, (new_time, movie_id))
                        
                        st.success(f"New show time added for '{selected_movie}': {new_time} on {new_date}")
                    else:
                        st.error("Failed to add show time.")
        else:
            st.info("No movies available in the database.")

    elif menu == "Movie List":
        st.subheader("📋 Current Movies")
        
        # Fetch all movies with details
        movies_query = """
        SELECT m.movie_id, m.movie_title, m.movie_description,
               GROUP_CONCAT(DISTINCT s.show_time ORDER BY s.show_time SEPARATOR ', ') as show_times,
               GROUP_CONCAT(DISTINCT s.show_date ORDER BY s.show_date SEPARATOR ', ') as show_dates,
               GROUP_CONCAT(DISTINCT sc.screen_name SEPARATOR ', ') as screens
        FROM movie m
        LEFT JOIN schedule s ON m.movie_id = s.movie_id
        LEFT JOIN movie_played_on_screen mps ON m.movie_id = mps.movie_id
        LEFT JOIN screen sc ON mps.screen_id = sc.screen_id
        GROUP BY m.movie_id
        """
        movies = execute_query(movies_query)
        
        if movies:
            for movie in movies:
                st.markdown(f"### {movie['movie_title']} (ID: {movie['movie_id']})")
                st.write(f"**Description:** {movie['movie_description']}")
                st.write(f"**Screens:** {movie['screens'] if movie['screens'] else 'None'}")
                st.write(f"**Show Dates:** {movie['show_dates'] if movie['show_dates'] else 'None'}")
                st.write(f"**Show Times:** {movie['show_times'] if movie['show_times'] else 'None'}")
                st.markdown("---")
        else:
            st.info("No movies available in the database.")

    st.sidebar.success("Admin Controls")
    
    # Logout button
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        spb.switch_page("Login")
        st.experimental_rerun()

if __name__ == "__main__":
    main()
