import time
import streamlit as st
import traceback

from config import DEFAULT_GROQ_API_KEY
from db.database import Database
from services.ai_assistant import AdaptLearnAssistant
from utils.tts import is_tts_available
from ui.rendering import apply_theme
from utils.animated_components import animated_title, animated_container, animated_header, animated_notification

# Import page modules with renamed import for profile to avoid name conflict
from ui.pages import start_page, dashboard, adapt_content
from ui.pages import profile as profile_page
from ui.pages import paths, history, quiz, pdf_content

def initialize_session_state():
    """Initialize or restore session state variables."""
    defaults = {
        "page": "start",
        "user_id": None,
        "username": None,
        "current_content_id": None,
        "original_text": "",
        "structured_description": "",
        "topic_input": "",
        "input_text_area_content": "",
        "current_adaptations": {},
        "current_profile": {
            "learning_style": "Visual",
            "disability_type": "None",
            "preferences": {
                "font_size": 12,
                "contrast": "Standard",
                "chunk_size": 200
            }
        },
        "start_time": None,
        "groq_api_key": DEFAULT_GROQ_API_KEY,
        "openai_api_key": "",
        "tts_audio_original": None,
        "tts_audio_simplified": None,
        "tts_audio_summary": None,
        "tts_audio_chunks": {},
        "visualization_image": None,
        "theme_loaded": False,  # Track if the theme has been loaded
        "show_welcome": True,   # Show welcome animation on first load
    }
    
    # Initialize any missing state variables
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Check if profile needs loading after potential state loss
    if st.session_state.user_id and isinstance(st.session_state.current_profile, dict) == False:
        try:
            temp_db = Database()
            st.session_state.current_profile = temp_db.get_user_profile(st.session_state.user_id)
            temp_db.close()
        except Exception:
            st.session_state.current_profile = defaults["current_profile"]

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Set up page configuration and apply theme
    st.set_page_config(page_title="Mentora!", page_icon="🧠", layout="wide")
    apply_theme()
    
    # Initialize database and assistant
    db = None
    assistant = None
    
    try:
        db = Database()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()
    
    # Set up API keys input in sidebar
    st.sidebar.subheader("API Keys")
    
    groq_api_key = st.sidebar.text_input(
        "Groq API Key", 
        value=st.session_state.groq_api_key, 
        type="password", 
        help="Enter your Groq API key from groq.com"
    )
    
    openai_api_key = st.sidebar.text_input(
        "OpenAI API Key (for DALL-E)",
        value=st.session_state.openai_api_key,
        type="password",
        help="Enter your OpenAI API key for DALL-E visualization features"
    )
    
    # Handle API key changes
    if groq_api_key != st.session_state.groq_api_key:
        st.session_state.groq_api_key = groq_api_key
        st.rerun()
        
    if openai_api_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        st.rerun()
    
    # Initialize assistant if API key is available
    if st.session_state.groq_api_key:
        try:
            assistant = AdaptLearnAssistant(
                api_key=st.session_state.groq_api_key, 
                db=db,
                openai_api_key=st.session_state.openai_api_key
            )
        except Exception as e:
            st.sidebar.error(f"Failed to initialize AI assistant: {e}")
            assistant = None
    
    # Navigation and Auth Functions
    def go_to_page(page_name):
        """Change the current page."""
        st.session_state.page = page_name
    
    def login_user(username, password):
        """Authenticate and log in a user."""
        user_id = db.authenticate_user(username, password)
        if user_id:
            st.session_state.user_id = user_id
            st.session_state.username = username
            st.session_state.current_profile = db.get_user_profile(user_id)
            go_to_page("dashboard")
            # Show welcome notification
            st.session_state.show_welcome = True
            st.rerun()
        return user_id is not None
    
    def register_user(username, password, email=None):
        """Register a new user."""
        user_id = db.create_user(username, password, email)
        if user_id:
            st.session_state.user_id = user_id
            st.session_state.username = username
            st.session_state.current_profile = db.get_user_profile(user_id)
            go_to_page("dashboard")
            # Show welcome notification
            st.session_state.show_welcome = True
            st.rerun()
        return user_id is not None
    
    def logout_user():
        """Log out the current user."""
        keys_to_del = [k for k in st.session_state if k not in ['groq_api_key', 'openai_api_key']]
        [st.session_state.pop(k) for k in keys_to_del]
        initialize_session_state()
        go_to_page("start")
        st.rerun()
    
    def reset_content_state():
        """Reset the content-related state variables."""
        keys_to_reset = [
            "current_content_id",
            "original_text",
            "structured_description",
            "topic_input",
            "input_text_area_content",
            "current_adaptations",
            "start_time",
            "tts_audio_original",
            "tts_audio_simplified",
            "tts_audio_summary",
            "tts_audio_chunks",
            "visualization_image"
        ]
        [st.session_state.pop(k, None) for k in keys_to_reset]
        st.session_state.input_text_area_content = ""
        st.session_state.current_adaptations = {}
        st.session_state.tts_audio_chunks = {}
    
    # Sidebar UI with Animations
    st.sidebar.markdown("""
    <style>
    @keyframes slideInRight {
        from { transform: translateX(30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .sidebar-title {
        color: #FF8C00;
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
        animation: slideInRight 0.7s ease-out;
    }
    </style>
    <div class="sidebar-title">Mentora! 🧠</div>
    """, unsafe_allow_html=True)
    
    # User info and login/logout
    if st.session_state.user_id:
        st.sidebar.markdown(f"""
        <style>
        @keyframes fadeInRight {{
            from {{ transform: translateX(20px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        .user-welcome {{
            background-color: #f8f8f8;
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #FF8C00;
            animation: fadeInRight 0.8s ease-out;
        }}
        .username {{
            font-weight: bold;
            color: #FF8C00;
        }}
        </style>
        <div class="user-welcome">
            Welcome, <span class="username">{st.session_state.username}</span>!
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.button("Logout", key="logout_btn", on_click=logout_user)
    else:
        st.sidebar.info("Please login or register to use the application.")
    
    # Navigation buttons with animations (only shown when logged in)
    if st.session_state.user_id:
        st.sidebar.markdown("---")
        
        st.sidebar.markdown("""
        <style>
        @keyframes fadeInUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .nav-header {
            color: #555555;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.8rem;
            animation: fadeInUp 0.6s ease-out;
        }
        </style>
        <div class="nav-header">Navigation</div>
        """, unsafe_allow_html=True)
        
        # Add animation delay to each button
        buttons = [
            {"name": "Dashboard", "key": "nav_dash", "page": "dashboard", "delay": 0.1},
            {"name": "Adapt Content", "key": "nav_adapt", "page": "adapt_content", "delay": 0.2},
            {"name": "PDF Content", "key": "nav_pdf", "page": "pdf_content", "delay": 0.3},
            {"name": "Quizzes", "key": "nav_quiz", "page": "quiz", "delay": 0.4},
            {"name": "Profile & Skills", "key": "nav_profile", "page": "profile", "delay": 0.5},
            {"name": "Learning Paths", "key": "nav_paths", "page": "paths", "delay": 0.6},
            {"name": "History", "key": "nav_history", "page": "history", "delay": 0.7}
        ]
        
        for button in buttons:
            st.sidebar.markdown(f"""
            <style>
            .nav-button-{button["key"]} {{
                animation: fadeInUp {0.6 + button["delay"]}s ease-out;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown(f'<div class="nav-button-{button["key"]}"></div>', unsafe_allow_html=True)
                st.sidebar.button(button["name"], key=button["key"], on_click=go_to_page, args=(button["page"],))
    
    # Settings section
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <style>
    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .settings-header {
        color: #555555;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.8rem;
        animation: fadeInUp 0.8s ease-out;
    }
    </style>
    <div class="settings-header">Settings</div>
    """, unsafe_allow_html=True)
    
    # Profile settings in sidebar (only shown when logged in)
    if st.session_state.user_id:
        with st.sidebar.expander("My Learning Profile"):
            user_profile = st.session_state.current_profile
            ls_opts = ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"]
            dis_opts = ["None", "Dyslexia", "Dyscalculia", "ADHD", "Dysgraphia", "Auditory Processing"]
            
            ls_idx = ls_opts.index(user_profile.get("learning_style", "Visual"))
            dis_idx = dis_opts.index(user_profile.get("disability_type", "None"))
            
            user_profile["learning_style"] = st.selectbox("Learning Style", ls_opts, index=ls_idx, key="p_ls_side")
            user_profile["disability_type"] = st.selectbox("Learning Needs", dis_opts, index=dis_idx, key="p_dis_side")
            
            pref = user_profile.setdefault("preferences", {})
            pref["chunk_size"] = st.slider("Chunk Size", 50, 500, pref.get("chunk_size", 150), 50, key="p_chunk_side")
            
            if st.button("Save Profile", key="save_p_side"):
                db.save_user_profile(st.session_state.user_id, user_profile)
                st.session_state.current_profile = user_profile
                
                # Show success notification
                animated_notification("Profile saved successfully!", type="success", duration=3)
                
                time.sleep(0.5)
                st.rerun()
    
    # TTS info
    if not is_tts_available():
        st.sidebar.info("Text-to-speech is disabled. Install gTTS for audio features: `pip install gtts`")
    
    # DALL-E info
    if not st.session_state.openai_api_key:
        st.sidebar.info("DALL-E visualization is disabled. Add your OpenAI API key for visual features.")

    # Welcome animation for newly logged in users
    if st.session_state.user_id and st.session_state.show_welcome:
        animated_notification(f"Welcome to Mentora!, {st.session_state.username}! 🎉", type="success", duration=4)
        st.session_state.show_welcome = False

    # Page Routing
    # Page Routing
    current_page = st.session_state.page
    
    # Protect pages that require login
    protected_pages = ["dashboard", "adapt_content", "profile", "paths", "history", "quiz", "pdf_content"]
    if current_page in protected_pages and not st.session_state.user_id:
        go_to_page("start")
        current_page = "start"
    
    # Warning if AI features are needed but not available
    ai_needed = current_page not in ["start", "history"]
    if ai_needed and not assistant:
        animated_notification("AI Assistant is unavailable. Please check your API key. Some features will be disabled.", 
                              type="warning", 
                              duration=5)

    # Main content rendering based on current page
    try:
        # Apply animated header for each page
        page_headers = {
            "start": {"title": "Welcome to Mentora!", "icon": "🧠", "subtitle": "Personalized adaptive learning platform"},
            "dashboard": {"title": "Dashboard", "icon": "📊", "subtitle": "Your learning overview"},
            "adapt_content": {"title": "Generate & Adapt Content", "icon": "✍️", "subtitle": "Create and personalize learning materials"},
            "pdf_content": {"title": "PDF Content Extractor", "icon": "📄", "subtitle": "Extract and adapt text from documents"},
            "profile": {"title": "Profile & Skills", "icon": "👤", "subtitle": "Your learning profile and skill progress"},
            "paths": {"title": "Learning Paths", "icon": "📚", "subtitle": "Structured learning journeys"},
            "history": {"title": "Interaction History", "icon": "📜", "subtitle": "Your past learning activities"},
            "quiz": {"title": "Quizzes", "icon": "📝", "subtitle": "Test your knowledge"}
        }
        
        # Don't show the animated header on the start/login page
        if current_page != "start" and st.session_state.user_id:
            header_info = page_headers.get(current_page, {"title": current_page.capitalize(), "icon": "🔍"})
            animated_header(
                title=header_info.get("title", ""),
                subtitle=header_info.get("subtitle", ""),
                icon=header_info.get("icon", ""),
                animation_type="slide"
            )
        
        # Render the appropriate page content
        if current_page == "start":
            start_page.render(db, go_to_page, login_user, register_user)
            
        elif current_page == "dashboard":
            def render_dashboard_content():
                dashboard.render(db, assistant, go_to_page, reset_content_state)
            
            animated_container(render_dashboard_content, animation_type="fade", delay=0.2)
            
        elif current_page == "adapt_content":
            adapt_content.render(db, assistant, reset_content_state)
            
        elif current_page == "pdf_content":
            pdf_content.render(db, assistant, reset_content_state)
            
        elif current_page == "profile":
            profile_page.render(db, assistant)
            
        elif current_page == "paths":
            paths.render(db, assistant, go_to_page, reset_content_state)
            
        elif current_page == "history":
            history.render(db)
            
        elif current_page == "quiz":
            quiz.render(db, assistant)
            
        else:
            st.error(f"Unknown page: {current_page}")
            go_to_page("start")
    
    except Exception as e:
        st.error("An application error occurred.")
        st.exception(e)
        traceback.print_exc()

if __name__ == "__main__":
    # Display TTS warning early if needed
    if not is_tts_available():
        st.warning("gTTS library is missing. Text-to-speech features will be disabled. Install using: `pip install gTTS`")
    
    # Display PyMuPDF warning if needed
    try:
        import fitz
    except ImportError:
        st.warning("PyMuPDF library is missing. PDF features will be disabled. Install using: `pip install pymupdf`")
    
    main()