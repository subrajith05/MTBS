import streamlit as st
import streamlit_extras.switch_page_button as spb
import hashlib
from db_utils import execute_query, execute_update

def main():
    st.set_page_config(page_title="Register", page_icon="📝", initial_sidebar_state="collapsed")

    st.title("ONLINE TICKET BOOKING SYSTEM")
    st.title("📝 Registration")

    # User registration form
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    contact = st.text_input("Contact Number")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        # Validate inputs
        if not all([first_name, last_name, email, contact, username, password, confirm_password]):
            st.error("All fields are required")
        elif password != confirm_password:
            st.error("Passwords do not match")
        else:
            # Check if username or email already exists
            check_query = "SELECT user_id FROM users WHERE username = %s OR email = %s"
            existing_user = execute_query(check_query, (username, email))
            
            if existing_user:
                st.error("Username or email already exists")
            else:
                # First create customer record
                customer_query = """
                INSERT INTO customer (first_name, last_name, customer_contact) 
                VALUES (%s, %s, %s)
                """
                customer_result = execute_update(customer_query, (first_name, last_name, email))
                
                if customer_result > 0:
                    # Get the new customer ID
                    customer_id_query = "SELECT LAST_INSERT_ID() as customer_id"
                    customer_id_result = execute_query(customer_id_query)
                    
                    if customer_id_result:
                        customer_id = customer_id_result[0]['customer_id']
                        
                        # Add to customer_cpy table
                        customer_cpy_query = """
                        INSERT INTO customer_cpy (customer_id, customer_contact) 
                        VALUES (%s, %s)
                        """
                        execute_update(customer_cpy_query, (customer_id, contact))
                        
                        # Create user account
                        # In a real app, you would hash the password properly
                        user_query = """
                        INSERT INTO users (username, email, password, customer_id, created_at) 
                        VALUES (%s, %s, %s, %s, NOW())
                        """
                        user_result = execute_update(user_query, (username, email, password, customer_id))
                        
                        if user_result > 0:
                            st.success("Registration successful! Please login.")
                            if st.button("Go to Login"):
                                spb.switch_page("Login")
                        else:
                            st.error("Failed to create user account")
                    else:
                        st.error("Failed to retrieve customer ID")
                else:
                    st.error("Failed to create customer record")

    # Login link
    st.markdown("---")
    st.write("Already have an account?")
    if st.button("Login"):
        spb.switch_page("Login")

if __name__ == "__main__":
    main()
