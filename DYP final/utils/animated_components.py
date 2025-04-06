import streamlit as st
import time

def animated_title(title, animation_type="fade"):
    """Display an animated title with various animation options."""
    animation_css = ""
    
    if animation_type == "fade":
        animation_css = """
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .animated-title { animation: fadeIn 1.2s ease-in-out; }
        """
    elif animation_type == "slide":
        animation_css = """
        @keyframes slideIn {
            from { transform: translateX(-50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .animated-title { animation: slideIn 1s ease-out; }
        """
    elif animation_type == "bounce":
        animation_css = """
        @keyframes bounce {
            0% { transform: translateY(-20px); opacity: 0; }
            50% { transform: translateY(10px); opacity: 0.7; }
            100% { transform: translateY(0); opacity: 1; }
        }
        .animated-title { animation: bounce 1.2s ease-in-out; }
        """
    elif animation_type == "highlight":
        animation_css = """
        @keyframes highlight {
            0% { text-shadow: 0 0 0 rgba(255, 140, 0, 0); color: #333; }
            30% { text-shadow: 0 0 20px rgba(255, 140, 0, 0.7); color: #FF8C00; }
            100% { text-shadow: 0 0 0 rgba(255, 140, 0, 0); color: #FF8C00; }
        }
        .animated-title { animation: highlight 2s ease-in-out; }
        """
    
    st.markdown(f"""
        <style>
        {animation_css}
        .animated-title {{
            color: #FF8C00;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }}
        </style>
        <h1 class="animated-title">{title}</h1>
    """, unsafe_allow_html=True)

def animated_container(content_func, animation_type="fade", delay=0):
    """Create a container with animation effects."""
    animation_css = ""
    
    if animation_type == "fade":
        animation_css = f"""
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        .animated-container {{ animation: fadeIn 1s ease-in-out {delay}s both; }}
        """
    elif animation_type == "slide-up":
        animation_css = f"""
        @keyframes slideUp {{
            from {{ transform: translateY(30px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        .animated-container {{ animation: slideUp 0.8s ease-out {delay}s both; }}
        """
    elif animation_type == "slide-right":
        animation_css = f"""
        @keyframes slideRight {{
            from {{ transform: translateX(-30px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        .animated-container {{ animation: slideRight 0.8s ease-out {delay}s both; }}
        """
    elif animation_type == "scale":
        animation_css = f"""
        @keyframes scale {{
            from {{ transform: scale(0.8); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}
        .animated-container {{ animation: scale 0.7s ease-out {delay}s both; }}
        """
    
    st.markdown(f"""
        <style>
        {animation_css}
        .animated-container {{
            background-color: #f8f8f8;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 5px solid #FF8C00;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }}
        </style>
        <div class="animated-container">
    """, unsafe_allow_html=True)
    
    # Execute the content function
    content_func()
    
    st.markdown("</div>", unsafe_allow_html=True)

def animated_progress(label, start_value=0, end_value=100, duration=1.5, color="#FF8C00"):
    """Display an animated progress bar that fills up over time."""
    # Create a placeholder for the progress bar
    progress_bar = st.progress(start_value)
    
    # Set up custom styling
    st.markdown(f"""
        <style>
        [data-testid="stProgressBar"] {{
            height: 20px;
            border-radius: 10px;
            transition: all 0.5s ease;
        }}
        [data-testid="stProgressBar"] > div {{
            background-color: {color};
        }}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**{label}**")
    
    # Animate the progress bar
    steps = 20  # Number of animation steps
    step_size = (end_value - start_value) / steps
    step_duration = duration / steps
    
    current = start_value
    for i in range(steps + 1):
        progress_bar.progress(int(current))
        current = min(current + step_size, end_value)
        time.sleep(step_duration)

def animated_metric(label, value, previous_value=None, animation_type="count", prefix="", suffix=""):
    """
    Display a metric with animation effects.
    
    Parameters:
        label: The label for the metric
        value: The current value to display
        previous_value: Optional previous value (for delta calculation)
        animation_type: 'count' (counting animation) or 'fade' (simple fade in)
        prefix: Optional prefix for the value (e.g., "$")
        suffix: Optional suffix for the value (e.g., "%")
    """
    # Convert to number if string with only digits
    if isinstance(value, str) and value.replace('.', '', 1).isdigit():
        value = float(value)
    
    formatted_value = f"{prefix}{value}{suffix}"
    
    # Calculate delta if previous value provided
    delta = None
    delta_color = "normal"
    if previous_value is not None and isinstance(value, (int, float)) and isinstance(previous_value, (int, float)):
        delta = value - previous_value
        delta_percent = (delta / previous_value * 100) if previous_value != 0 else 0
        delta_text = f"{delta_percent:.1f}%"
        delta_color = "inverse" if delta < 0 else "normal"
    
    # Create empty placeholder for the metric
    metric_placeholder = st.empty()
    
    if animation_type == "count" and isinstance(value, (int, float)):
        # Count up animation
        steps = 20  # Number of animation steps
        step_duration = 0.03  # Duration per step in seconds
        
        start_val = 0
        for i in range(steps + 1):
            current_val = start_val + (value - start_val) * (i / steps)
            current_formatted = f"{prefix}{current_val:.1f}{suffix}" if isinstance(current_val, float) else f"{prefix}{int(current_val)}{suffix}"
            if delta is not None:
                metric_placeholder.metric(label, current_formatted, delta_text, delta_color=delta_color)
            else:
                metric_placeholder.metric(label, current_formatted)
            time.sleep(step_duration)
    else:
        # Simple fade-in animation (CSS-based)
        st.markdown("""
            <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            [data-testid="metric-container"] {
                animation: fadeIn 0.8s ease-out;
            }
            </style>
        """, unsafe_allow_html=True)
        
        if delta is not None:
            metric_placeholder.metric(label, formatted_value, delta_text, delta_color=delta_color)
        else:
            metric_placeholder.metric(label, formatted_value)

def animated_card(title, content, icon=None, color="#FF8C00", animation="slide-up"):
    """Display content in an animated card with custom styling."""
    animation_css = ""
    if animation == "slide-up":
        animation_css = """
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .custom-card { animation: slideUp 0.7s ease-out; }
        """
    elif animation == "fade":
        animation_css = """
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .custom-card { animation: fadeIn 0.8s ease-in-out; }
        """
    elif animation == "scale":
        animation_css = """
        @keyframes scaleIn {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .custom-card { animation: scaleIn 0.6s ease-out; }
        """
    
    icon_html = f'<span class="card-icon">{icon}</span>' if icon else ''
    
    st.markdown(f"""
        <style>
        {animation_css}
        .custom-card {{
            background-color: #f8f8f8;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 5px solid {color};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }}
        .custom-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.12);
        }}
        .card-title {{
            color: {color};
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        .card-icon {{
            margin-right: 10px;
            font-size: 1.4rem;
        }}
        .card-content {{
            color: #333333;
        }}
        </style>
        <div class="custom-card">
            <div class="card-title">{icon_html}{title}</div>
            <div class="card-content">{content}</div>
        </div>
    """, unsafe_allow_html=True)

def create_animated_tabs(tabs_list):
    """
    Create animated tabs with custom styling.
    Returns the selected tab index.
    
    Example:
    tab_names = ["Overview", "Details", "Settings"]
    selected = create_animated_tabs(tab_names)
    if selected == 0:
        st.write("Overview content")
    elif selected == 1:
        st.write("Details content")
    elif selected == 2:
        st.write("Settings content")
    """
    st.markdown("""
    <style>
    @keyframes slideDown {
        from { transform: translateY(-10px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        animation: slideDown 0.5s ease-out;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f5f5f5;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        color: #555555;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f0f0f0;
        color: #FF8C00;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF8C00 !important;
        color: #ffffff !important;
        transform: translateY(-3px);
        box-shadow: 0 4px 10px rgba(255, 140, 0, 0.3);
    }
    .stTabs [data-baseweb="tab-panel"] {
        animation: fadeIn 0.6s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the tabs
    tabs = st.tabs(tabs_list)
    
    # Return the tabs object for content to be added
    return tabs

def animated_header(title, subtitle=None, icon=None, animation_type="slide"):
    """
    Display an animated header with title, optional subtitle, and icon.
    
    Parameters:
        title: The main title text
        subtitle: Optional subtitle text
        icon: Optional icon (emoji or HTML)
        animation_type: Animation style ('slide', 'fade', or 'scale')
    """
    animation_css = ""
    
    if animation_type == "slide":
        animation_css = """
        @keyframes slideHeader {
            from { transform: translateX(-30px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .header-container { animation: slideHeader 0.8s ease-out; }
        .header-subtitle { animation: slideHeader 1s ease-out; }
        """
    elif animation_type == "fade":
        animation_css = """
        @keyframes fadeHeader {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .header-container { animation: fadeHeader 1s ease-in-out; }
        .header-subtitle { animation: fadeHeader 1.4s ease-in-out; }
        """
    elif animation_type == "scale":
        animation_css = """
        @keyframes scaleHeader {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .header-container { animation: scaleHeader 0.7s ease-out; }
        .header-subtitle { animation: scaleHeader 0.9s ease-out; }
        """
    
    icon_html = icon if icon else ""
    subtitle_html = f'<div class="header-subtitle">{subtitle}</div>' if subtitle else ""
    
    st.markdown(f"""
        <style>
        {animation_css}
        .header-container {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }}
        .header-icon {{
            font-size: 2rem;
            margin-right: 15px;
            color: #FF8C00;
        }}
        .header-title {{
            color: #FF8C00;
            font-size: 2.2rem;
            font-weight: bold;
        }}
        .header-subtitle {{
            color: #777777;
            font-size: 1.2rem;
            margin-top: 5px;
            margin-bottom: 15px;
        }}
        </style>
        <div class="header-container">
            <div class="header-icon">{icon_html}</div>
            <div class="header-title">{title}</div>
        </div>
        {subtitle_html}
        <hr style="margin-bottom: 20px; border-color: #eee;">
    """, unsafe_allow_html=True)

def animated_image(image_path, caption=None, width=None, animation="fade"):
    """
    Display an image with animation effects.
    
    Parameters:
        image_path: Path to the image file
        caption: Optional caption text
        width: Optional width (in pixels)
        animation: Animation style ('fade', 'slide', 'scale', or 'rotate')
    """
    width_style = f"width: {width}px;" if width else "max-width: 100%;"
    animation_css = ""
    
    if animation == "fade":
        animation_css = """
        @keyframes fadeImage {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .animated-image { animation: fadeImage 1s ease-in-out; }
        """
    elif animation == "slide":
        animation_css = """
        @keyframes slideImage {
            from { transform: translateX(-30px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .animated-image { animation: slideImage 0.8s ease-out; }
        """
    elif animation == "scale":
        animation_css = """
        @keyframes scaleImage {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .animated-image { animation: scaleImage 0.7s ease-out; }
        """
    elif animation == "rotate":
        animation_css = """
        @keyframes rotateImage {
            from { transform: rotate(-5deg) scale(0.9); opacity: 0; }
            to { transform: rotate(0) scale(1); opacity: 1; }
        }
        .animated-image { animation: rotateImage 0.8s ease-out; }
        """
    
    caption_html = f'<div class="image-caption">{caption}</div>' if caption else ""
    
    st.markdown(f"""
        <style>
        {animation_css}
        .image-container {{
            margin-bottom: 20px;
        }}
        .animated-image {{
            {width_style}
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}
        .animated-image:hover {{
            transform: scale(1.02);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }}
        .image-caption {{
            color: #777777;
            font-size: 0.9rem;
            margin-top: 8px;
            text-align: center;
            font-style: italic;
        }}
        </style>
        <div class="image-container">
            <img src="{image_path}" class="animated-image" alt="{caption or 'Image'}">
            {caption_html}
        </div>
    """, unsafe_allow_html=True)

def animated_text_reveal(text, delay=0.05, container_style=None):
    """
    Display text with a typewriter-like animation effect.
    
    Parameters:
        text: The text to display
        delay: Delay between each character (in seconds)
        container_style: Optional CSS styling for the container
    """
    import time
    
    # Create an empty placeholder
    text_placeholder = st.empty()
    
    # Apply container style if provided
    if container_style:
        text_placeholder.markdown(f"<div style='{container_style}'></div>", unsafe_allow_html=True)
    
    # Display the text character by character
    for i in range(len(text) + 1):
        text_placeholder.markdown(f"<div style='{container_style or ''}'>{text[:i]}</div>", unsafe_allow_html=True)
        time.sleep(delay)

def animated_notification(message, type="info", icon=None, duration=3):
    """
    Display an animated notification message that automatically disappears.
    
    Parameters:
        message: The notification message
        type: 'info', 'success', 'warning', or 'error'
        icon: Optional icon to display
        duration: Time in seconds before notification disappears
    """
    if type == "info":
        color = "#3498db"
        bg_color = "#e8f4fd"
        icon = icon or "ℹ️"
    elif type == "success":
        color = "#FF8C00"  # Orange for our theme
        bg_color = "#fff4e8"
        icon = icon or "✅"
    elif type == "warning":
        color = "#f39c12"
        bg_color = "#fef6e6"
        icon = icon or "⚠️"
    elif type == "error":
        color = "#e74c3c"
        bg_color = "#fde8e6"
        icon = icon or "❌"
    
    # Create placeholder for notification
    notification = st.empty()
    
    # Display notification with animation
    notification.markdown(f"""
        <style>
        @keyframes slideInRight {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes fadeOut {{
            from {{ opacity: 1; }}
            to {{ opacity: 0; }}
        }}
        .notification {{
            padding: 12px 20px;
            background-color: {bg_color};
            color: {color};
            border-left: 4px solid {color};
            border-radius: 6px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            animation: slideInRight 0.5s ease-out, fadeOut 0.5s ease-in {duration}s forwards;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }}
        .notification-icon {{
            margin-right: 12px;
            font-size: 1.2rem;
        }}
        .notification-message {{
            flex-grow: 1;
        }}
        </style>
        <div class="notification">
            <div class="notification-icon">{icon}</div>
            <div class="notification-message">{message}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Clear notification after duration
    import threading
    threading.Timer(duration + 0.5, notification.empty).start()

def animated_features(features_list, columns=2):
    """
    Display a list of features with animations and icons.
    
    Parameters:
        features_list: List of dictionaries with 'title', 'description', and 'icon' keys
        columns: Number of columns to display features in
    """
    st.markdown("""
        <style>
        @keyframes featureAppear {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .features-container {
            display: flex;
            flex-wrap: wrap;
            margin: 0 -10px;
        }
        .feature-item {
            background-color: #f8f8f8;
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            animation: featureAppear 0.8s ease-out;
            animation-fill-mode: both;
        }
        .feature-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 15px;
            color: #FF8C00;
        }
        .feature-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333333;
        }
        .feature-description {
            color: #555555;
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Calculate width percentage based on columns
    col_width = 100 / columns - 2  # Subtract margin
    
    # Start container
    st.markdown('<div class="features-container">', unsafe_allow_html=True)
    
    # Add each feature with staggered animation delay
    for i, feature in enumerate(features_list):
        delay = i * 0.1  # Stagger the animations
        
        st.markdown(f"""
            <div class="feature-item" style="flex: 0 0 {col_width}%; animation-delay: {delay}s;">
                <div class="feature-icon">{feature.get('icon', '🔍')}</div>
                <div class="feature-title">{feature.get('title', '')}</div>
                <div class="feature-description">{feature.get('description', '')}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # End container
    st.markdown('</div>', unsafe_allow_html=True)

def loading_animation(message="Loading...", style="dots"):
    """
    Display a custom loading animation.
    
    Parameters:
        message: The loading message
        style: 'dots', 'spinner', or 'progress'
    """
    animation_css = ""
    animation_html = ""
    
    if style == "dots":
        animation_css = """
        @keyframes dotsAnimation {
            0% { content: "."; }
            33% { content: ".."; }
            66% { content: "..."; }
            100% { content: ""; }
        }
        .loading-dots::after {
            content: "";
            display: inline-block;
            width: 20px;
            text-align: left;
            animation: dotsAnimation 1.5s infinite;
        }
        """
        animation_html = f'<div class="loading-container"><span class="loading-message">{message}</span><span class="loading-dots"></span></div>'
    elif style == "spinner":
        animation_css = """
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #FF8C00;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1.5s linear infinite;
            display: inline-block;
            margin-right: 10px;
            vertical-align: middle;
        }
        """
        animation_html = f'<div class="loading-container"><div class="spinner"></div><span class="loading-message">{message}</span></div>'
    elif style == "progress":
        animation_css = """
        @keyframes progressAnimation {
            0% { width: 0%; }
            50% { width: 100%; }
            100% { width: 0%; }
        }
        .progress-bar {
            background-color: #f3f3f3;
            height: 4px;
            border-radius: 2px;
            width: 100%;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-bar-inner {
            background-color: #FF8C00;
            height: 100%;
            width: 0%;
            animation: progressAnimation 2s ease-in-out infinite;
        }
        """
        animation_html = f"""
        <div class="loading-container">
            <span class="loading-message">{message}</span>
            <div class="progress-bar">
                <div class="progress-bar-inner"></div>
            </div>
        </div>
        """
    
    # Create a placeholder for the loading animation
    placeholder = st.empty()
    
    # Display the animation
    placeholder.markdown(f"""
        <style>
        {animation_css}
        .loading-container {{
            padding: 20px;
            background-color: #f8f8f8;
            border-radius: 8px;
            margin: 20px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            text-align: center;
        }}
        .loading-message {{
            color: #555;
            font-size: 1.1rem;
            margin-bottom: 10px;
        }}
        </style>
        {animation_html}
    """, unsafe_allow_html=True)
    
    return placeholder