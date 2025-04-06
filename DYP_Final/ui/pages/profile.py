import streamlit as st

def render(db, assistant):
    """Render the user profile and skills page."""
    st.title("Profile & Skills")
    
    # Profile editing section
    st.subheader("Learning Profile")
    profile = st.session_state.current_profile
    
    # Learning style selection
    ls_options = ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"]
    ls_index = ls_options.index(profile.get("learning_style", "Visual"))
    profile["learning_style"] = st.selectbox(
        "Learning Style", 
        ls_options, 
        index=ls_index, 
        key="prof_ls_main",
        help="Select your primary learning style to optimize content presentation."
    )
    
    # Disability/needs selection
    dis_options = ["None", "Dyslexia", "Dyscalculia", "ADHD", "Dysgraphia", "Auditory Processing"]
    dis_index = dis_options.index(profile.get("disability_type", "None"))
    profile["disability_type"] = st.selectbox(
        "Learning Needs", 
        dis_options, 
        index=dis_index, 
        key="prof_dis_main",
        help="Select any specific learning need for specialized content adaptations."
    )
    
    # Preferences
    pref = profile.setdefault("preferences", {})
    pref["chunk_size"] = st.slider(
        "Content Chunk Size", 
        50, 500, 
        pref.get("chunk_size", 150), 
        50, 
        key="prof_chunk_main",
        help="Controls how content is broken into smaller pieces, especially helpful for ADHD."
    )
    
    # Save button
    if st.button("Save Profile", key="save_prof_main"):
        db.save_user_profile(st.session_state.user_id, profile)
        st.session_state.current_profile = profile
        st.success("Profile saved successfully!")

    # Skills analysis section 
    st.markdown("---")
    st.subheader("Skill Analysis")
    skill_data = db.get_user_skills(st.session_state.user_id)
    
    if not skill_data:
        st.info("Interact with content to build your skills profile.")
    else:
        # AI Analysis if available
        if assistant:
            analysis_data = assistant.get_analysis_and_recommendations(st.session_state.user_id)
            if analysis_data:
                st.markdown("#### AI Analysis")
                st.markdown(
                    f"<div class='recommendation-card'>{analysis_data['analysis_text']}</div>", 
                    unsafe_allow_html=True
                )
        
        # Show proficiency by category
        st.markdown("#### Proficiency")
        categories = {}
        [categories.setdefault(cat, []).append(
            {'id': sid, 'name': name, 'prof': prof, 'count': count}
        ) for sid, name, cat, prof, count in skill_data]
        
        for cat, skills in categories.items():
            with st.expander(f"{cat.replace('_', ' ').title()} ({len(skills)})", expanded=True):
                cols = st.columns(3)
                for i, skill in enumerate(sorted(skills, key=lambda x: x['prof'], reverse=True)):
                    col = cols[i % 3]
                    with col:
                        prof_p = skill['prof'] * 100
                        clr = "#a6e3a1" if prof_p > 70 else "#eed49f" if prof_p > 40 else "#ed8796"
                        st.markdown(
                            f"""<div style='background-color:#363a4f; padding:10px; border-radius:8px; margin-bottom:8px;'>
                                <b>{skill['name']}</b><br>
                                <div style='background-color:#494d64; height:8px; border-radius:4px; margin:5px 0;'>
                                    <div style='background-color:{clr}; width:{prof_p}%; height:8px; border-radius:4px;'></div>
                                </div>
                                <small>Proficiency: {prof_p:.1f}% | Times practiced: {skill['count']}</small>
                            </div>""", 
                            unsafe_allow_html=True
                        )

    # Learning path generator section
    st.markdown("---")
    st.subheader("Learning Path Generator")
    weak_skills_path = db.get_user_weakest_skills(st.session_state.user_id, 3)
    
    if weak_skills_path and assistant:
        focus = ", ".join([f"'{n}'" for _, n, _, _ in weak_skills_path])
        st.write(f"Target skills: {focus}")
        steps = st.slider("Number of steps:", 3, 10, 5, key="path_steps")
        
        if st.button("Generate My Learning Path", type="primary", key="gen_path_prof"):
            with st.spinner("Generating personalized learning path..."):
                path_id, path_text = assistant.generate_personalized_learning_path(
                    st.session_state.user_id, 
                    focus, 
                    steps
                )
                
            if path_id:
                st.success("Learning path created successfully!")
                st.markdown(path_text)
                st.info("View your learning paths in the 'Learning Paths' section.")
            else:
                st.error(f"Failed to create learning path: {path_text}")
    elif not assistant:
        st.info("API key needed for AI-powered learning path generation.")
    else:
        st.info("Practice with more content to identify areas for improvement.")