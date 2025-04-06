import streamlit as st
from ui.rendering import render_skill_chart
from utils.animated_components import animated_metric, animated_card, loading_animation, animated_features

def render(db, assistant, go_to_page, reset_content_state):
    """Render the dashboard page."""
    
    # Skills snapshot section with animated metrics
    st.markdown("### Snapshot")
    
    # Show loading animation while fetching data
    loading_placeholder = loading_animation("Loading your learning data...", style="spinner")
    
    # Fetch data
    progress = db.get_user_progress_stats(st.session_state.user_id)
    
    # Also get quiz stats if available
    quiz_stats = db.get_quiz_stats(st.session_state.user_id) if hasattr(db, 'get_quiz_stats') else None
    
    # Remove loading animation
    loading_placeholder.empty()
    
    # Display metrics in two rows with animations
    row1_cols = st.columns(3)
    with row1_cols[0]:
        animated_metric("Content Interactions", progress['total_interactions'], animation_type="count")
    with row1_cols[1]:
        animated_metric("Content Viewed", progress['content_pieces_interacted'], animation_type="count")
    with row1_cols[2]:
        animated_metric("Avg Feedback", f"{progress['average_score']*100:.1f}%", suffix="%")
    
    # Add quiz metrics if available
    if quiz_stats and quiz_stats['total_attempts'] > 0:
        st.markdown("### Quiz Performance")
        row2_cols = st.columns(3)
        with row2_cols[0]:
            animated_metric("Quizzes Taken", quiz_stats['completed_quizzes'], animation_type="count")
        with row2_cols[1]:
            animated_metric("Correct Answers", quiz_stats['total_correct_answers'], animation_type="count")
        with row2_cols[2]:
            animated_metric("Quiz Avg Score", f"{quiz_stats['average_score']*100:.1f}%", suffix="%")
    
    # Skills visualization section
    st.markdown("### Skills")
    c_ch, c_det = st.columns([2, 1])
    with c_ch:
        strong = db.get_user_strongest_skills(st.session_state.user_id, 5)
        weak = db.get_user_weakest_skills(st.session_state.user_id, 5)
        disp = strong + weak
        if disp:
            fig = render_skill_chart(disp, "Strengths & Weaknesses")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chart error or insufficient data.")
        else:
            st.info("Interact with more content to build your skills profile.")
            
    with c_det:
        st.markdown("#### Strengths")
        if strong:
            [st.markdown(f"<div class='skill-badge'>{n} ({p:.1f})</div>", unsafe_allow_html=True) 
             for _, n, _, p in strong]
        else:
            st.caption("None yet.")
            
        st.markdown("#### Areas to Improve")
        if weak:
            [st.markdown(f"<div class='weak-badge'>{n} ({p:.1f})</div>", unsafe_allow_html=True) 
             for _, n, _, p in weak]
        else:
            st.caption("None yet.")
            
        if st.button("Full Profile", key="d_v_p"):
            go_to_page("profile")
    
    # Recommendations section with animated cards
    st.markdown("### Next Steps")
    
    # Animated features section showing app capabilities
    if progress['total_interactions'] < 3:
        # For new users, show features
        st.markdown("#### Getting Started")
        features = [
            {
                "title": "Adapt Content",
                "description": "Generate or paste learning content and adapt it to your learning style.",
                "icon": "📝"
            },
            {
                "title": "PDF Extraction",
                "description": "Upload PDF documents and extract content for adaptation.",
                "icon": "📄"
            },
            {
                "title": "Take Quizzes",
                "description": "Test your knowledge with personalized quizzes.",
                "icon": "❓"
            },
            {
                "title": "Visualizations",
                "description": "Get visual representations of complex concepts with DALL-E.",
                "icon": "🖼️"
            }
        ]
        animated_features(features, columns=4)
    
    r_c1, r_c2, r_c3 = st.columns(3)
    
    with r_c1:
        st.markdown("#### Content Suggestions")
        rec_c = db.get_recommended_content(st.session_state.user_id)
        if rec_c:
            for i, (c_id, t, _, top) in enumerate(rec_c[:2]):  # Reduced to show only 2 for space
                animated_card(
                    title=t or f"Content: {top}",
                    content=f"Recommended content to improve your skills",
                    icon="📚",
                    animation="slide-up" if i == 0 else "slide-up",
                    color="#FF8C00"
                )
                if st.button("View", key=f"d_a_{c_id}"):
                    c_data = db.get_content_piece(c_id)
                    if c_data:
                        reset_content_state()
                        st.session_state.current_content_id = c_id
                        st.session_state.original_text = c_data[1]
                        st.session_state.structured_description = c_data[2]
                        st.session_state.input_text_area_content = c_data[1]
                        st.session_state.topic_input = c_data[4] or ""
                        go_to_page("adapt_content")
                        st.rerun()
        else:
            st.info("Explore more content to get personalized recommendations.")
            
    with r_c2:
        st.markdown("#### Quiz Recommendations")
        if hasattr(db, 'get_recommended_quizzes'):
            rec_quizzes = db.get_recommended_quizzes(st.session_state.user_id, limit=2)
            if rec_quizzes:
                for i, quiz in enumerate(rec_quizzes):
                    animated_card(
                        title=quiz['title'],
                        content=f"{quiz['topic']} • {quiz['difficulty']}",
                        icon="📝",
                        animation="slide-up",
                        color="#FF9E33"
                    )
                
                if st.button("Take a Quiz", type="primary"):
                    go_to_page("quiz")
            else:
                st.info("Create a quiz to get started!")
                if st.button("Create Quiz"):
                    go_to_page("quiz")
        else:
            st.info("Quiz feature unavailable.")
            
    with r_c3:
        st.markdown("#### Learning Focus")
        if assistant:
            with st.spinner("Generating recommendations..."):
                rec_t = assistant.generate_recommendations_text(st.session_state.user_id)
            
            animated_card(
                title="Personalized Recommendations",
                content=rec_t,
                icon="💡",
                animation="slide-up",
                color="#a6e3a1"
            )
            
            if st.button("Generate Learning Path", key="d_g_p"):
                go_to_page("profile")
        else:
            st.info("API key needed for AI-powered recommendations.")
    
    # Quick access buttons
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➡️ Adapt New Content", use_container_width=True):
            reset_content_state()
            go_to_page("adapt_content")
            
    with col2:
        if st.button("📝 Take a Quiz", use_container_width=True):
            go_to_page("quiz")
            
    with col3:
        if st.button("📚 View Learning Paths", use_container_width=True):
            go_to_page("paths")