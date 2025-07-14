import mysql.connector
from mysql.connector import Error
import streamlit as st

# Create a connection pool or cache the connection in session state
def get_database_connection():
    # Check if connection exists in session state
    if 'db_conn' not in st.session_state:
        try:
            # Replace these with your actual database credentials
            connection = mysql.connector.connect(
                host='localhost',
                database='movie',
                user='root',  # Replace with your MySQL username
                password='subu1209'   # Replace with your MySQL password
            )
            
            if connection.is_connected():
                st.session_state['db_conn'] = connection
                return connection
                
        except Error as e:
            st.error(f"Error connecting to MySQL database: {e}")
            return None
    else:
        # Return existing connection from session state
        connection = st.session_state['db_conn']
        if not connection.is_connected():
            # Reconnect if connection was closed
            connection.reconnect()
        return connection

# Execute SELECT queries and return results
def execute_query(query, params=None):
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            st.error(f"Error executing query: {e}")
            return None
    return None

# Execute INSERT, UPDATE, DELETE queries
def execute_update(query, params=None):
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Error as e:
            st.error(f"Error executing update: {e}")
            return 0
    return 0

# Close database connection when app is done
def close_connection():
    if 'db_conn' in st.session_state and st.session_state['db_conn'].is_connected():
        st.session_state['db_conn'].close()
        del st.session_state['db_conn']
