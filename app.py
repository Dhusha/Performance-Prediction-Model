import streamlit as st
import mysql.connector
import bcrypt
import datetime
import re
import pytz
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# MySQL Connection
connection = mysql.connector.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port=4000,
    user="................",
    password="............"
)

mycursor = connection.cursor(buffered=True)

mycursor.execute("CREATE DATABASE IF NOT EXISTS PerformancePrediction")
mycursor.execute('USE PerformancePrediction')

mycursor.execute('''CREATE TABLE IF NOT EXISTS User_data
                    (id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    registered_date TIMESTAMP,
                    last_login TIMESTAMP)''')

def username_exists(username):
    mycursor.execute("SELECT * FROM User_data WHERE username = %s", (username,))
    return mycursor.fetchone() is not None

def email_exists(email):
    mycursor.execute("SELECT * FROM User_data WHERE email = %s", (email,))
    return mycursor.fetchone() is not None

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_user(username, password, email, registered_date):
    if username_exists(username):
        return 'username_exists'
    
    if email_exists(email):
        return 'email_exists'
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    mycursor.execute(
        "INSERT INTO User_data (username, password, email, registered_date) VALUES (%s, %s, %s, %s)",
        (username, hashed_password, email, registered_date)
    )
    connection.commit()
    return 'success'

def verify_user(username, password):
    mycursor.execute("SELECT password FROM User_data WHERE username = %s", (username,))
    record = mycursor.fetchone()
    if record and bcrypt.checkpw(password.encode('utf-8'), record[0].encode('utf-8')):
        mycursor.execute("UPDATE User_data SET last_login = %s WHERE username = %s", (datetime.datetime.now(pytz.timezone('Asia/Kolkata')), username))
        connection.commit()
        return True
    return False

def reset_password(username, new_password):
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    mycursor.execute(
        "UPDATE User_data SET password = %s WHERE username = %s",
        (hashed_password, username)
    )
    connection.commit()

# Session state management
if 'sign_up_successful' not in st.session_state:
    st.session_state.sign_up_successful = False
if 'login_successful' not in st.session_state:
    st.session_state.login_successful = False
if 'reset_password' not in st.session_state:
    st.session_state.reset_password = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

# Page styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f0f2f6;
    }
    .big-font {
        font-size: 36px !important;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 30px;
        text-align: center;
    }
    .stButton > button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 0;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #1565C0;
    }
    .stTextInput > div > div > input {
        border-radius: 5px;
        border: 2px solid #90CAF9;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1E88E5;
        box-shadow: 0 0 0 1px #1E88E5;
    }
    .link-text {
        color: #1E88E5;
        text-align: center;
        cursor: pointer;
        transition: color 0.3s ease;
    }
    .link-text:hover {
        color: #1565C0;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# Login page
def login():
    st.markdown('<p class="big-font">Performance Nexus 🎯</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form(key='login_form', clear_on_submit=True):
            username = st.text_input(label='Username', placeholder='Enter Username')
            password = st.text_input(label='Password', placeholder='Enter Password', type='password')

            st.markdown("<br>", unsafe_allow_html=True)

            if st.form_submit_button('Login'):
                if not username or not password:
                    st.error("Please enter all credentials")
                elif verify_user(username, password):
                    st.success(f"Welcome, {username}!")
                    st.session_state.login_successful = True
                    st.session_state.username = username
                    st.session_state.current_page = 'home'
                    st.experimental_rerun()
                else:
                    st.error("Incorrect username or password. Please try again or sign up if you don't have an account.")

        if not st.session_state.get('login_successful', False):
            st.markdown("<br>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("<div class='link-text'>New user?</div>", unsafe_allow_html=True)
                if st.button('Sign Up'):
                    st.session_state.current_page = 'sign_up'
                    st.experimental_rerun()
            with col_b:
                st.markdown("<div class='link-text'>Forgot Password?</div>", unsafe_allow_html=True)
                if st.button('Reset Password'):
                    st.session_state.current_page = 'reset_password'
                    st.experimental_rerun()

# Sign up page
def signup():
    st.markdown('<p class="big-font">Sign Up for Performance Prediction</p>', unsafe_allow_html=True)

    with st.form(key='signup_form', clear_on_submit=True):
        email = st.text_input(label='Email', placeholder='Enter Your Email')
        username = st.text_input(label='Username', placeholder='Enter Your Username')
        password = st.text_input(label='Password', placeholder='Enter Your Password', type='password')
        re_password = st.text_input(label='Confirm Password', placeholder='Confirm Your Password', type='password')

        if st.form_submit_button('Sign Up'):
            if not email or not username or not password or not re_password:
                st.error("Enter all the Credentials")
            elif len(password) <= 3:
                st.error("Password too short")
            elif password != re_password:
                st.error("Passwords do not match! Please Re-enter")
            else:
                result = create_user(username, password, email, datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
                if result == 'success':
                    st.success("Account created successfully!")
                    st.session_state.sign_up_successful = True
                    st.session_state.current_page = 'login'
                    st.experimental_rerun()

    if not st.session_state.get('sign_up_successful', False):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='link-text'>Already have an account?</div>", unsafe_allow_html=True)
        if st.button('Login'):
            st.session_state.current_page = 'login'
            st.experimental_rerun()

# Reset password page
def reset_password_page():
    st.markdown('<p class="big-font">Reset Password</p>', unsafe_allow_html=True)

    with st.form(key='reset_password_form', clear_on_submit=True):
        username = st.text_input(label='Username', value='', placeholder='Enter your username')
        new_password = st.text_input(label='New Password', type='password', placeholder='Enter new password')
        re_password = st.text_input(label='Confirm New Password', type='password', placeholder='Confirm new password')

        if st.form_submit_button('Reset Password'):
            if not username:
                st.error("Enter your username.")
            elif not username_exists(username):
                st.error("Username not found. Enter a valid username.")
            elif not new_password or not re_password:
                st.error("Enter new password and confirm password.")
            elif new_password != re_password:
                st.error("Passwords do not match. Please re-enter.")
            else:
                reset_password(username, new_password)
                st.success("Password reset successful. You can now login with your new password.")
                st.session_state.reset_password = False
                st.session_state.current_page = 'login'
                st.experimental_rerun()

    if not st.session_state.get('reset_password', False):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='link-text'>Back to Login?</div>", unsafe_allow_html=True)
        if st.button('Login'):
            st.session_state.current_page = 'login'
            st.experimental_rerun()
def home_page():
    st.markdown(f'<p class="big-font">Welcome to the Performance Nexus Dashboard, {st.session_state.username}!</p>', unsafe_allow_html=True)

    # Sidebar for user input (unchanged)
    st.sidebar.header("Input Parameters")
    employee_name = st.sidebar.text_input("Employee Name", "")
    employee_id = st.sidebar.text_input("Employee ID", "")
    employee_age = st.sidebar.number_input("Employee Age", min_value=18, max_value=100, value=25)
    employee_joining_date = st.sidebar.date_input("Employee Joining Date", datetime.date.today())
    employee_last_appraisal_date = st.sidebar.date_input("Last Appraisal Date", datetime.date.today())

    # Submit button
    if st.sidebar.button("Submit"):
        st.session_state.submitted = True

    # Main dashboard area
    if not st.session_state.get('submitted', False):
        # Display image only before submission
        st.image("homepageimage1.webp", use_column_width=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.write("Please enter employee details in the sidebar and click 'Submit' to view the performance report.")
    else:
        # After submission, show the report
        tab1, tab2 = st.tabs(["Performance Report", "Performance Insights"])
        
        with tab1:
            st.markdown("## Employee Performance Report")
            st.markdown(f"**Employee Name:** {employee_name}")
            st.markdown(f"**Employee ID:** {employee_id}")
            st.markdown(f"**Age:** {employee_age}")
            st.markdown(f"**Joining Date:** {employee_joining_date}")
            st.markdown(f"**Last Appraisal Date:** {employee_last_appraisal_date}")
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                performance_score = np.random.randint(60, 100)
                st.metric("Predicted Performance", f"{performance_score}%", "4%")
                
                def create_stylized_gauge_chart(performance_score):
                    colors = ['#FF4B4B', '#FFA14B', '#FFE74B', '#8DED8E', '#4BFF4B']
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=performance_score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Employee Performance", 'font': {'size': 24}},
                        gauge={
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                            'bar': {'color': "darkblue"},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "gray",
                            'steps': [
                                {'range': [0, 20], 'color': colors[0]},
                                {'range': [20, 40], 'color': colors[1]},
                                {'range': [40, 60], 'color': colors[2]},
                                {'range': [60, 80], 'color': colors[3]},
                                {'range': [80, 100], 'color': colors[4]}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': performance_score
                            }
                        }
                    ))
                    
                    fig.update_layout(
                        font={'color': "darkblue", 'family': "Arial"},
                        height=300,
                        width=300,
                        margin=dict(l=20, r=20, t=30, b=20),
                        paper_bgcolor="white",
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    return fig

                fig = create_stylized_gauge_chart(performance_score)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Key Factors Influencing Performance")
                factors = pd.DataFrame({
                    'Factor': ['Experience', 'Training', 'Projects', 'Teamwork'],
                    'Impact': [0.3, 0.25, 0.28, 0.17]
                })
                fig = px.bar(factors, x='Impact', y='Factor', orientation='h',
                             color='Impact', color_continuous_scale='Viridis')
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("Performance Trend")
            dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="M")
            performance = np.random.randint(70, 100, size=len(dates))
            trend_data = pd.DataFrame({"Date": dates, "Performance": performance})
            fig = px.line(trend_data, x="Date", y="Performance", 
                          line_shape="spline", render_mode="svg")
            fig.update_traces(line_color='#1E88E5')
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.markdown("## Performance Insights")
            st.write(f"Based on the analysis for Employee ID {employee_id}:")
            st.write(f"- Current performance is {'above' if performance_score > 80 else 'below'} average")
            st.write(f"- Key area for improvement: {'Training' if performance_score < 80 else 'Project Management'}")
            st.write(f"- Recommended action: {'Enroll in advanced skills program' if performance_score < 80 else 'Take on leadership role in upcoming project'}")
            
            st.markdown("### Detailed Analysis")
            st.write("1. **Performance Trend:**")
            st.write("   The employee's performance has shown a steady increase over the past year, with notable improvements in the last quarter.")
            
            st.write("2. **Strengths:**")
            st.write("   - Strong project management skills")
            st.write("   - Excellent team collaboration")
            st.write("   - High adaptability to new technologies")
            
            st.write("3. **Areas for Improvement:**")
            st.write("   - Time management in high-pressure situations")
            st.write("   - Technical documentation skills")
            
            st.write("4. **Recommendations:**")
            st.write("   - Enroll in an advanced project management certification course")
            st.write("   - Assign as a mentor for junior team members to further develop leadership skills")
            st.write("   - Provide opportunities to lead cross-functional projects")

        # Logout button
        if st.button("Logout"):
            st.session_state.login_successful = False
            st.session_state.username = ''
            st.session_state.current_page = 'login'
            st.experimental_rerun()



# Main app logic
if st.session_state.current_page == 'login':
    login()
elif st.session_state.current_page == 'sign_up':
    signup()
elif st.session_state.current_page == 'reset_password':
    reset_password_page()
elif st.session_state.current_page == 'home':
    home_page()
else:
    st.error("Page not found or not implemented yet.")
