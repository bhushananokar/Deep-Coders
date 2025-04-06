import time
import streamlit as st

def render(db, assistant, go_to_page, reset_content_state):
    """Render the learning paths page."""
    st.title("📚 My Learning Paths")
    
    # Existing learning paths
    paths = db.get_learning_paths_for_user(st.session_state.user_id)
    if not paths:
        st.info("You don't have any learning paths yet. Generate one from your profile page or below.")
    else:
        st.subheader("Saved Learning Paths")
        
        for pid, title, desc, focus, created in paths:
            with st.expander(f"{title} (Focus: {focus}) - {created[:10]}", expanded=False):
                st.markdown(f"*Description:* {desc}")
                
                # Path content items
                path_c = db.get_learning_path_content(pid)
                if not path_c:
                    st.write("No content in this path yet.")
                else:
                    st.markdown("##### Learning Steps:")
                    for i, (cid, ct, _, ctop) in enumerate(path_c):
                        st.markdown(f"**{i+1}: {ct or f'Content: {ctop}'}**")
                        
                        if st.button("View Content", key=f"adapt_path_{cid}"):
                            c_data = db.get_content_piece(cid)
                            if c_data:
                                reset_content_state()
                                st.session_state.current_content_id = cid
                                st.session_state.original_text = c_data[1]
                                st.session_state.structured_description = c_data[2]
                                st.session_state.input_text_area_content = c_data[1]
                                st.session_state.topic_input = c_data[4] or ""
                                go_to_page("adapt_content")
                                st.rerun()
                    st.markdown("---")
    
    # Generate new path section
    st.markdown("---")
    st.subheader("Generate New Learning Path")
    
    weak = db.get_user_weakest_skills(st.session_state.user_id, 3)
    if weak and assistant:
        focus = ", ".join([f"'{n}'" for _, n, _, _ in weak])
        st.write(f"Target skills: {focus}")
        
        if st.button("Generate Learning Path", key="gen_path_paths"):
            with st.spinner("Generating personalized learning path..."):
                path_id, path_text = assistant.generate_personalized_learning_path(
                    st.session_state.user_id, 
                    focus, 
                    5
                )
                
            if path_id:
                st.success("Learning path created successfully!")
                st.markdown(path_text)
                time.sleep(2)  # Give user time to see the success message
                st.rerun()
            else:
                st.error(f"Failed to create learning path: {path_text}")
    elif not assistant:
        st.info("API key needed for AI-powered learning path generation.")
    else:
        st.info("Interact with more content to identify improvement areas for learning paths.")