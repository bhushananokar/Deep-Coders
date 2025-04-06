import streamlit as st
from utils.animated_components import animated_title, animated_features, animated_card

def render(db, go_to_page, login_user, register_user):
    """Render the start/login/registration page."""
    # Custom animated title
    animated_title("Welcome to Mentora!", animation_type="highlight")
    
    if not st.session_state.user_id:
        # Animated login/register tabs
        st.markdown("""
        <style>
        @keyframes fadeInUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .stTabs {
            animation: fadeInUp 0.7s ease-out;
        }
        </style>
        """, unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["Login", "Register"])
        with t1:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                s = st.form_submit_button("Login")
            if s:
                if not u or not p:
                    st.error("Username and password required.")
                elif not db:
                    st.error("Database connection failed.")
                elif not login_user(u, p):
                    st.error("Invalid credentials.")
        with t2:
            with st.form("reg"):
                u = st.text_input("Username*")
                e = st.text_input("Email (Optional)")
                p = st.text_input("Password*", type="password")
                c = st.text_input("Confirm Password*", type="password")
                s = st.form_submit_button("Register")
            if s:
                if not u or not p:
                    st.error("Username and password are required.")
                elif p != c:
                    st.error("Passwords don't match.")
                elif not db:
                    st.error("Database connection failed.")
                elif not register_user(u, p, e or None):
                    st.error("Username may already be taken.")
    else:
        go_to_page("dashboard")
        st.rerun()
    
    # Animated feature cards
    st.markdown("---")
    st.markdown("## Personalized AI Learning")
    
    features = [
        {
            "title": "Adaptive Content",
            "description": "Content tailored to your learning style and needs, with visualizations and simplified formats",
            "icon": "📚"
        },
        {
            "title": "PDF Processing",
            "description": "Upload and extract text from PDF documents for adaptation and learning",
            "icon": "📄"
        },
        {
            "title": "Visual Learning",
            "description": "DALL-E powered visualizations for complex concepts and instructions",
            "icon": "🖼️"
        },
        {
            "title": "Personalized Quizzes",
            "description": "Test your knowledge with quizzes tailored to your learning profile",
            "icon": "📝"
        }
    ]
    
    animated_features(features, columns=2)
    
    # Learning styles section
    st.markdown("## Learning Styles and Accommodations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        animated_card(
            title="Learning Styles",
            content="""
            AdaptLearn supports various learning styles:
            • Visual learners through diagrams & illustrations
            • Auditory learners with text-to-speech
            • Kinesthetic learners via interactive elements
            • Reading/Writing learners with structured content
            """,
            icon="🧠",
            animation="slide-up",
            color="#FF8C00"
        )
    
    with col2:
        animated_card(
            title="Learning Accommodations",
            content="""
            Special accommodations for:
            • Dyslexia: Simplified text and syllable breakdowns
            • Dyscalculia: Visual math representations
            • ADHD: Content chunking for better focus
            • And more...
            """,
            icon="♿",
            animation="slide-up",
            color="#a6e3a1"
        )
    
    # Footer with animated call to action
    st.markdown("""
    <style>
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .cta-container {
        background-color: #fff4e8;
        border-radius: 10px;
        padding: 20px;
        margin: 30px 0;
        text-align: center;
        border: 2px solid #FF8C00;
        animation: pulse 2s infinite;
    }
    .cta-heading {
        color: #FF8C00;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .cta-text {
        color: #333333;
        font-size: 1.1rem;
        margin-bottom: 0;
    }
    </style>
    <div class="cta-container">
        <div class="cta-heading">Ready to Enhance Your Learning Experience?</div>
        <p class="cta-text">Sign up today to start your personalized learning journey!</p>
    </div>
    """, unsafe_allow_html=True)