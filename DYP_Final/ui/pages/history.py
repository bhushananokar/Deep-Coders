import streamlit as st

def render(db):
    """Render the user interaction history page."""
    st.title("📜 Interaction History")
    
    # Get user interactions
    interactions = db.get_user_recent_interactions(st.session_state.user_id, 50)
    
    if not interactions:
        st.info("No interactions recorded yet. Adapt content to start building your history.")
    else:
        # Create a dataframe for display
        st.dataframe(
            interactions, 
            use_container_width=True, 
            column_config={
                "created_at": "Timestamp", 
                "title": "Content", 
                "interaction_type": "Interaction Type", 
                "feedback_rating": st.column_config.NumberColumn(
                    "Rating ⭐", 
                    format="%d"
                ), 
                "score": st.column_config.ProgressColumn(
                    "Score", 
                    format="%.2f", 
                    min_value=0.0, 
                    max_value=1.0
                )
            }
        )
        
        # Progress statistics
        st.subheader("Progress Summary")
        progress = db.get_user_progress_stats(st.session_state.user_id)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Interactions", progress['total_interactions'])
        c2.metric("Content Pieces", progress['content_pieces_interacted'])
        c3.metric("Average Score", f"{progress['average_score']*100:.1f}%")
        
        # Add more detailed stats if available
        if progress['total_interactions'] > 0:
            st.markdown(f"You've provided positive feedback {progress['positive_feedback_count']} times, which is "
                      f"{progress['positive_feedback_count']/progress['total_interactions']*100:.1f}% of your interactions.")