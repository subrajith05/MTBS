import streamlit as st
from datetime import datetime as dt
import datetime
import random
import streamlit_extras.switch_page_button as spb
from db_utils import execute_query, execute_update

def check_authentication():
    # Check if user is logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.error("Please login to access this page.")
        st.stop()

def main():
    st.set_page_config(page_title="User Dashboard", page_icon="👤", layout="wide", initial_sidebar_state="collapsed")
    
    # Verify user authentication
    check_authentication()
    
    # Get user information
    customer_id = st.session_state.get('customer_id')
    username = st.session_state.get('username', 'User')
    
    st.title("👤 User Dashboard")
    st.write(f"Welcome, {username}! Enjoy your experience.")
    
    # Set page config
    st.title("Movies Available")

    # Custom CSS for bigger buttons
    st.markdown(
        """
        <style>
            div.stButton > button {
                width: 100%;
                height: 50px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                background-color: #444;
                color: white;
                border: none;
                cursor: pointer;
            }
            div.stButton > button:hover {
                background-color: #666;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<h2 style='text-align: center;'>🎬 Movies Available For Showing</h2>", unsafe_allow_html=True)

    # Get today's date
    today = datetime.date.today()
    
    # Fetch movies from database with their schedule
    movies_query = """
    SELECT DISTINCT m.movie_id, m.movie_title, m.movie_description, m.poster_url,
        MIN(s.show_date) as start_date, MAX(s.show_date) as stop_date,
        GROUP_CONCAT(DISTINCT TIME_FORMAT(s.show_time, '%h:%i %p') ORDER BY s.show_time SEPARATOR ',') as show_times,
        sc.screen_name, sc.screen_number
    FROM movie m
    LEFT JOIN schedule s ON m.movie_id = s.movie_id
    LEFT JOIN movie_played_on_screen mps ON m.movie_id = mps.movie_id
    LEFT JOIN screen sc ON mps.screen_id = sc.screen_id
    GROUP BY m.movie_id, sc.screen_name, sc.screen_number
    """
    
    movie_data = execute_query(movies_query)
    
    if not movie_data:
        st.warning("No movies are currently available.")
    else:
        # Process movie data
        movies = []
        for movie in movie_data:
            # Format show times
            show_times = movie['show_times'].split(',') if movie['show_times'] else []
            
            # Create details string
            screen_info = f"{movie['screen_name']} (Screen {movie['screen_number']})" if movie['screen_name'] else "Standard Screen"
            details = f"{screen_info}"
            
            # Create movie dictionary
            movie_obj = {
                "id": movie['movie_id'],
                "name": movie['movie_title'],
                "details": details,
                "shows": show_times,
                "start_date": movie['start_date'],
                "stop_date": movie['stop_date'],
                "description": movie['movie_description'],
                "poster_url": movie['poster_url']
            }
            movies.append(movie_obj)
        
        # Filter available movies (those with start_date <= today <= stop_date)
        available_movies = [movie for movie in movies if movie["stop_date"] and movie["stop_date"] >= today]
        
        if not available_movies:
            st.warning("No movies are currently scheduled for showing.")
        else:
            # Display movies in rows of 6
            for i in range(0, len(available_movies), 6):
                cols = st.columns(6)
                for j, movie in enumerate(available_movies[i:i+6]):
    
                    with cols[j % 6]:
                        if movie.get("poster_url"):
                            st.image(movie["poster_url"], width=200)

                        if st.button(movie["name"], key=f"movie_{movie['id']}"):
                            st.session_state["selected_movie"] = movie  
                            st.session_state["selected_date"] = None  
                            st.session_state["selected_show"] = None  
                            st.session_state["selected_gold_seats"] = []  
                            st.session_state["selected_standard_seats"] = []  
                            st.session_state["num_seats"] = 1  # Default value
                            st.rerun()

    # Step 2: Show Movie Details & Date Selection
    if "selected_movie" in st.session_state:
        movie = st.session_state["selected_movie"]
        st.markdown(f"## {movie['name']}")
        if movie.get("poster_url"):
            st.image(movie["poster_url"], width=300)
        st.write(movie["details"])
        st.write(movie["description"])

        # Step 3: Date Selection
        min_date = max(movie["start_date"], today) if movie["start_date"] else today
        max_date = movie["stop_date"] if movie["stop_date"] else today
        
        selected_date = st.date_input(
            "📅 Select a Date:",
            min_value=min_date,
            max_value=max_date,
            value=min_date
        )

        if selected_date:
            st.session_state["selected_date"] = selected_date

        # Step 4: Showtimes Selection
        if "selected_date" in st.session_state:
            # Get showtimes for this specific date from database
            show_query = """
            SELECT TIME_FORMAT(show_time, '%h:%i %p') as formatted_time, show_time 
            FROM schedule 
            WHERE movie_id = %s AND show_date = %s
            ORDER BY show_time
            """
            show_data = execute_query(show_query, (movie["id"], st.session_state["selected_date"]))
            
            available_shows = []
            actual_times = []
            
            if show_data:
                current_date = datetime.date.today()
                current_time = dt.now().time()
                selected_date = st.session_state["selected_date"]
                
                for show in show_data:
                    show_time_str = show['formatted_time']
                    show_time_obj = dt.strptime(show_time_str, "%I:%M %p").time()
                    
                    # If selected date is in the future, show all times
                    # If selected date is today, only show times that haven't started yet
                    if selected_date > current_date or (selected_date == current_date and show_time_obj > current_time):
                        available_shows.append(show['formatted_time'])
                        actual_times.append(show['show_time'])
                
                st.markdown(f"### 🎟 Available Shows on {st.session_state['selected_date']}")
                
                # Check if available_shows is not empty before creating columns
                if available_shows:
                    show_cols = st.columns(len(available_shows))
                    for i, show in enumerate(available_shows):
                        with show_cols[i]:
                            if st.button(show, key=f"show_{i}"):
                                st.session_state["selected_show"] = show
                                st.session_state["actual_show_time"] = actual_times[i] 
                                st.session_state["selected_gold_seats"] = []
                                st.session_state["selected_standard_seats"] = []
                                st.session_state["num_seats"] = 1 
                                st.rerun()
                else:
                    if selected_date == current_date:
                        st.info(f"No shows available for {st.session_state['selected_date']} at this time. All shows for today may have already started.")
                    else:
                        st.info(f"No shows scheduled for {st.session_state['selected_date']}.")
            else:
                st.info(f"No shows scheduled for {st.session_state['selected_date']}. Please select another date.")
    # Step 5: Seat Selection
    if "selected_show" in st.session_state and "selected_date" in st.session_state:
        st.markdown(f"## 🎥 Selected Show: {st.session_state['selected_show']} on {st.session_state['selected_date']}")
        st.markdown("### 🏟 Select Your Seats")

        # Get the screen info for this movie
        screen_query = """
        SELECT sc.screen_id, sc.screen_name, sc.number_of_seats 
        FROM screen sc
        JOIN movie_played_on_screen mps ON sc.screen_id = mps.screen_id
        WHERE mps.movie_id = %s
        LIMIT 1
        """
        screen_data = execute_query(screen_query, (st.session_state["selected_movie"]["id"],))
        
        if screen_data:
            screen_id = screen_data[0]["screen_id"]
            total_seats = screen_data[0]["number_of_seats"]
            screen_name = screen_data[0]["screen_name"]
            
            # Split seats between gold and standard (e.g., 30% gold, 70% standard)
            gold_seats_count = int(total_seats * 0.3)
            standard_seats_count = total_seats - gold_seats_count
            
            # Only fetch booked seats if we have actual_show_time
            booked_gold_seats = []
            booked_standard_seats = []
            
            if "actual_show_time" in st.session_state:
                # Get already booked seats for this show
                booked_query = """
                SELECT ticket_id, gold_seats, standard_seats
                FROM tickets
                WHERE movie_id = %s AND show_date = %s AND show_time = %s
                """
                booked_data = execute_query(
                    booked_query, 
                    (st.session_state["selected_movie"]["id"], 
                    st.session_state["selected_date"],
                    st.session_state["actual_show_time"])
                )
                
                # Process booked seats
                if booked_data:
                    for booking in booked_data:
                        if booking['gold_seats']:
                            booked_gold_seats.extend([int(x) for x in booking['gold_seats'].split(',')])
                        if booking['standard_seats']:
                            booked_standard_seats.extend([int(x) for x in booking['standard_seats'].split(',')])
            
            # Number of seats selector
            num_seats = st.number_input(
                "🎟 How many seats do you need?",
                min_value=1,
                max_value=10,
                step=1,
                value=st.session_state.get("num_seats", 1)
            )
            st.session_state["num_seats"] = num_seats
            
            # Initialize seat selections if not already in session state
            if "selected_gold_seats" not in st.session_state:
                st.session_state["selected_gold_seats"] = []
            if "selected_standard_seats" not in st.session_state:
                st.session_state["selected_standard_seats"] = []
            
            # Gold seats section
            gold_seats = list(range(1, gold_seats_count + 1))
            st.markdown("### ⭐ Gold Seats")
            gold_cols = st.columns(6)
            for i, seat in enumerate(gold_seats):
                with gold_cols[i % 6]:
                    # Check if seat is already booked
                    is_booked = seat in booked_gold_seats
                    is_selected = seat in st.session_state["selected_gold_seats"]
                    
                    # Determine button color and state
                    if is_booked:
                        st.button(f"{seat} 🚫", key=f"gold_{seat}", disabled=True)
                    else:
                        button_label = f"{seat} ✅" if is_selected else str(seat)
                        if st.button(button_label, key=f"gold_{seat}"):
                            if is_selected:
                                st.session_state["selected_gold_seats"].remove(seat)
                            elif len(st.session_state["selected_gold_seats"]) + len(st.session_state["selected_standard_seats"]) < num_seats:
                                st.session_state["selected_gold_seats"].append(seat)
                            st.rerun()
            
            # Standard seats section
            standard_seats = list(range(1, standard_seats_count + 1))
            st.markdown("### 💺 Standard Seats")
            std_cols = st.columns(6)
            for i, seat in enumerate(standard_seats):
                with std_cols[i % 6]:
                    # Check if seat is already booked
                    is_booked = seat in booked_standard_seats
                    is_selected = seat in st.session_state["selected_standard_seats"]
                    
                    # Determine button color and state
                    if is_booked:
                        st.button(f"{seat} 🚫", key=f"std_{seat}", disabled=True)
                    else:
                        button_label = f"{seat} ✅" if is_selected else str(seat)
                        if st.button(button_label, key=f"std_{seat}"):
                            if is_selected:
                                st.session_state["selected_standard_seats"].remove(seat)
                            elif len(st.session_state["selected_gold_seats"]) + len(st.session_state["selected_standard_seats"]) < num_seats:
                                st.session_state["selected_standard_seats"].append(seat)
                            st.rerun()
            
            # Display selected seats summary
            st.markdown(f"### ✅ Selected Gold Seats: {sorted(st.session_state['selected_gold_seats'])}")
            st.markdown(f"### ✅ Selected Standard Seats: {sorted(st.session_state['selected_standard_seats'])}")
            
            # Calculate pricing
           # Calculate pricing
            gold_price = 150  # Base price for gold seats
            standard_price = 100  # Base price for standard seats

            total_selected_seats = len(st.session_state["selected_gold_seats"]) + len(st.session_state["selected_standard_seats"])
            total_gold_cost = len(st.session_state["selected_gold_seats"]) * gold_price
            total_standard_cost = len(st.session_state["selected_standard_seats"]) * standard_price
            base_cost = total_gold_cost + total_standard_cost

            # Calculate convenience fee
            convenience_fee = 10 * total_selected_seats  # Rs. 10 per ticket

            # Calculate GST (18%)
            gst_amount = 0.18 * base_cost

            # Calculate final total
            total_cost = base_cost + gst_amount + convenience_fee

            # Display pricing breakdown
            st.markdown("### 💰 Pricing Details")
            st.write(f"Base Ticket Cost: ₹{base_cost}")
            st.write(f"GST (18%): ₹{gst_amount:.2f}")
            st.write(f"Convenience Fee (₹10/ticket): ₹{convenience_fee}")
            st.write(f"**Total Cost: ₹{total_cost:.2f}**")

            # Confirm Booking and Payment
            total_selected = len(st.session_state["selected_gold_seats"]) + len(st.session_state["selected_standard_seats"])
            if total_selected > 0:
                if total_selected == num_seats:
                    # Add Payment Interface
                    st.markdown("---")
                    st.markdown("### 💳 Payment Details")
                    
                    payment_method = st.radio(
                        "Select Payment Method:",
                        ["Credit Card", "Debit Card", "UPI"],
                        horizontal=True
                    )
                    
                    if payment_method in ["Credit Card", "Debit Card"]:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            card_number = st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX")
                            card_holder = st.text_input("Card Holder Name")
                        
                        with col2:
                            expiry = st.text_input("Expiry Date (MM/YY)", placeholder="MM/YY")
                            cvv = st.text_input("CVV", type="password", max_chars=3)
                    
                    elif payment_method == "UPI":
                        upi_id = st.text_input("UPI ID", placeholder="username@upi")
                    
                    # Payment button - This replaces the original "Confirm Booking" button
                    if st.button("💰 Make Payment", key="payment_button"):
                        # Show processing spinner
                        with st.spinner("Processing payment..."):
                            import time
                            time.sleep(5)  # Simulate payment processing
                            
                            # Generate ticket ID
                            ticket_id = f"TKT-{st.session_state['selected_movie']['id']}-{random.randint(1000,9999)}"
                            
                            # Save tickets to database
                            gold_seats_str = ','.join(str(seat) for seat in st.session_state["selected_gold_seats"])
                            standard_seats_str = ','.join(str(seat) for seat in st.session_state["selected_standard_seats"])
                            
                            ticket_query = """
                            INSERT INTO tickets 
                            (ticket_id, show_time, show_date, screen_id, cost, base_cost, gst_amount, convenience_fee, 
                            payment_method, gold_seats, standard_seats, movie_id, movie_title, customer_id) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            
                            ticket_result = execute_update(
                                ticket_query, 
                                (
                                    ticket_id,
                                    st.session_state["actual_show_time"],
                                    st.session_state["selected_date"],
                                    screen_id,
                                    total_cost,
                                    base_cost,
                                    gst_amount,
                                    convenience_fee,
                                    payment_method,
                                    gold_seats_str if gold_seats_str else None,
                                    standard_seats_str if standard_seats_str else None,
                                    st.session_state["selected_movie"]["id"],
                                    st.session_state["selected_movie"]["name"],
                                    customer_id
                                )
                            )
                            
                            if ticket_result > 0:
                                st.success(f"🎉 Payment Successful! Booking Confirmed!")
                                st.markdown("### 🎟️ Ticket Details")
                                st.write(f"**Ticket ID:** {ticket_id}")
                                st.write(f"**Movie:** {st.session_state['selected_movie']['name']}")
                                st.write(f"**Date:** {st.session_state['selected_date']}")
                                st.write(f"**Show Time:** {st.session_state['selected_show']}")
                                st.write(f"**Screen:** {screen_name}")
                                st.write(f"**Gold Seats:** {sorted(st.session_state['selected_gold_seats'])}")
                                st.write(f"**Standard Seats:** {sorted(st.session_state['selected_standard_seats'])}")
                                
                                # Display payment details
                                st.markdown("### 💰 Payment Details")
                                st.write(f"Base Ticket Cost: ₹{base_cost}")
                                st.write(f"GST (18%): ₹{gst_amount:.2f}")
                                st.write(f"Convenience Fee: ₹{convenience_fee}")
                                st.write(f"**Total Paid: ₹{total_cost:.2f}**")
                                
                                # Clear selection after successful booking
                                if st.button("🔄 Book Another Ticket"):
                                    for key in ["selected_movie", "selected_date", "selected_show", "selected_gold_seats", "selected_standard_seats"]:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    st.rerun()
                            else:
                                st.error("Payment failed. Please try again.")
                else:
                    st.warning(f"Please select exactly {num_seats} seats to continue.")
            else:
                st.info("Please select seats to continue.")
        else:
            st.error("Screen information not available for this movie.")

    # Show booked tickets (My Tickets section)
    if "customer_id" in st.session_state and "selected_movie" not in st.session_state:
        st.markdown("---")
        st.markdown("## 🎟 My Tickets")
        
        tickets_query = """
        SELECT ticket_id, movie_title, show_date, TIME_FORMAT(show_time, '%h:%i %p') as formatted_time,
               gold_seats, standard_seats, cost 
        FROM tickets 
        WHERE customer_id = %s
        ORDER BY show_date DESC, show_time DESC
        """
        tickets = execute_query(tickets_query, (st.session_state["customer_id"],))
        
        if tickets and len(tickets) > 0:
            for ticket in tickets:
                with st.expander(f"🎬 {ticket['movie_title']} - {ticket['show_date']} - {ticket['formatted_time']}"):
                    st.write(f"**Ticket ID:** {ticket['ticket_id']}")
                    st.write(f"**Gold Seats:** {ticket['gold_seats'] if ticket['gold_seats'] else 'None'}")
                    st.write(f"**Standard Seats:** {ticket['standard_seats'] if ticket['standard_seats'] else 'None'}")
                    st.write(f"**Cost:** ₹{ticket['cost']}")
        else:
            st.info("You haven't booked any tickets yet.")
            
    # Go Back Option
    if "selected_movie" in st.session_state and st.button("🔙 Go Back", key="go_back"):
        st.session_state.pop("selected_movie", None)
        st.session_state.pop("selected_date", None)
        st.session_state.pop("selected_show", None)
        st.session_state.pop("selected_gold_seats", None)
        st.session_state.pop("selected_standard_seats", None)
        st.rerun()
    
    # Logout button in sidebar
    st.sidebar.title("User Options")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        spb.switch_page("Login")
        st.experimental_rerun()

if __name__ == "__main__":
    main()
