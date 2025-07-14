import streamlit as st
import streamlit_extras.switch_page_button as spb
import hashlib
from db_utils import execute_query

def verify_password(stored_password, input_password):
    # In a real application, you would use a secure password hashing library
    # This is just a simple example - use bcrypt or similar in production
    hashed_input = hashlib.sha256(input_password.encode()).hexdigest()
    return hashed_input == stored_password

def main():
    st.set_page_config(page_title="Login Page", page_icon="🔒", initial_sidebar_state="collapsed")

    st.title("ONLINE TICKET BOOKING SYSTEM")

    st.title("🔒 Login Page")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    mode = st.radio("Select an option:", ["Admin", "User"])

    if st.button("Login"):
        if mode == "Admin":
            # Query admin table via users table with admin role
            query = """
            SELECT u.user_id, u.username, u.password, a.admin_id, a.admin_role 
            FROM users u 
            JOIN admin a ON u.customer_id = a.admin_id 
            WHERE u.username = %s
            """
            results = execute_query(query, (username,))
            
            if results and len(results) > 0:
                stored_password = results[0]['password']
                
                # In a real app, you would use a secure password verification method
                if password == stored_password:  # For simplicity - use proper password hashing in production
                    st.session_state['user_id'] = results[0]['user_id']
                    st.session_state['admin_id'] = results[0]['admin_id']
                    st.session_state['admin_role'] = results[0]['admin_role']
                    st.session_state['logged_in'] = True
                    st.session_state['is_admin'] = True
                    
                    st.success("Login successful! Redirecting...")
                    spb.switch_page("admin")
                else:
                    st.error("Invalid password")
            else:
                st.error("Admin username not found")
                
        elif mode == "User":
            # Query users table for regular user
            query = """
            SELECT user_id, username, password, customer_id 
            FROM users 
            WHERE username = %s
            """
            results = execute_query(query, (username,))
            
            if results and len(results) > 0:
                stored_password = results[0]['password']
                
                # In a real app, you would use a secure password verification method
                if password == stored_password:  # For simplicity - use proper password hashing in production
                    st.session_state['user_id'] = results[0]['user_id']
                    st.session_state['customer_id'] = results[0]['customer_id']
                    st.session_state['logged_in'] = True
                    st.session_state['is_admin'] = False
                    
                    st.success("Login successful! Redirecting...")
                    spb.switch_page("user")
                else:
                    st.error("Invalid password")
            else:
                st.error("Username not found")

    # Adding register option
    st.markdown("---")
    st.write("Don't have an account?")
    if st.button("Register"):
        spb.switch_page("register")  # You'll need to create this page

if __name__ == "__main__":
    main()
