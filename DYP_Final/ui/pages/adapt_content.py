import time
import asyncio
import streamlit as st
import re
import os
from PIL import Image

from utils.helpers import extract_mermaid_code
from utils.tts import generate_tts_audio, is_tts_available

def render(db, assistant, reset_content_state):
    """Render the adapt content page."""
    st.title("✍️ Generate & Adapt Content")
    
    if not assistant:
        st.warning("API key required. Enter a valid API key in the sidebar to use AI features.")
    
    col1, col2 = st.columns([1, 1])
    
    # Input column
    with col1:
        st.header("Input")
        
        # Content generation section
        with st.expander("Generate New Content", expanded=not st.session_state.input_text_area_content):
            topic_input = st.text_input("Topic:", value=st.session_state.topic_input, key="topic_in")
            st.session_state.topic_input = topic_input  # Update state
            
            if st.button("Generate", key="gen_btn", disabled=not assistant):
                if not topic_input:
                    st.warning("Please enter a topic.")
                else:
                    with st.spinner(f"Generating content for '{topic_input}'..."):
                        gen_text = assistant.generate_content_from_topic(topic_input)
                        if gen_text:
                            reset_content_state()
                            st.session_state.input_text_area_content = gen_text
                            st.session_state.original_text = gen_text
                            st.session_state.topic_input = topic_input
                            struct_desc = assistant.structure_content_description(gen_text)
                            title = (topic_input or "Generated")[:50]
                            st.session_state.current_content_id = db.store_content_piece(
                                title, gen_text, struct_desc, 'generated', topic_input
                            )
                            skills = assistant.identify_content_skills(gen_text)
                            if skills:
                                db.map_content_skills(st.session_state.current_content_id, skills)
                            st.session_state.start_time = time.time()
                            st.success("Content generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate content. Please try again.")
        
        # Paste/Edit section
        st.subheader("Paste / Edit Content")
        input_text = st.text_area(
            "Content:", 
            value=st.session_state.input_text_area_content, 
            height=400, 
            key="input_text"
        )
        
        # Handle edits
        if input_text != st.session_state.input_text_area_content:
            st.session_state.input_text_area_content = input_text
            if st.session_state.current_content_id and input_text != st.session_state.original_text:
                st.info("Content edited. Context has been reset.")
                reset_content_state()
                st.session_state.input_text_area_content = input_text
        
        # DALL-E Visualization section
        with st.expander("Generate Visualization", expanded=False):
            if assistant and hasattr(assistant, 'dalle_visualizer') and assistant.dalle_visualizer:
                st.markdown("Generate a visual representation of a key concept from your content using DALL-E.")
                
                # Option to extract concept automatically or enter manually
                concept_option = st.radio(
                    "Concept Selection",
                    ["Extract automatically", "Enter manually"],
                    key="concept_option"
                )
                
                if concept_option == "Enter manually":
                    concept_input = st.text_input("Concept to visualize:", key="concept_manual")
                else:
                    concept_input = ""  # Will be extracted automatically
                
                if st.button("Generate Visualization", key="viz_btn"):
                    current_text = st.session_state.input_text_area_content
                    if not current_text:
                        st.warning("Please enter or generate some content first.")
                    else:
                        if concept_option == "Extract automatically":
                            # Extract concept from text
                            with st.spinner("Analyzing content to identify key concept..."):
                                sys_p = "Educational content analyst. Identify the most important concept to visualize."
                                user_p = f"Identify the single most important concept from this text that would benefit from visualization:\n{current_text[:1000]}\nConcept to visualize:"
                                
                                response = assistant._send_request(
                                    "llama3-8b-8192",  # Use a faster model for extraction
                                    [
                                        {"role": "system", "content": sys_p},
                                        {"role": "user", "content": user_p}
                                    ],
                                    temperature=0.3
                                )
                                
                                if response and 'choices' in response and response['choices']:
                                    concept_input = response['choices'][0]['message']['content']
                                    st.success(f"Extracted concept: {concept_input}")
                                else:
                                    st.error("Failed to extract concept. Please enter one manually.")
                                    st.stop()
                        
                        # Generate visualization
                        with st.spinner(f"Generating visualization for: {concept_input}"):
                            img_path, message = assistant.generate_visualization(
                                concept_input, 
                                context=current_text[:500]
                            )
                            
                            if img_path:
                                # Store the path in session state for display
                                st.session_state.visualization_image = img_path
                                st.success("Visualization generated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to generate visualization: {message}")
            else:
                st.info("DALL-E visualization requires an OpenAI API key. Please add it in the sidebar settings.")
        
        # Show current visualization if available
        if 'visualization_image' in st.session_state and st.session_state.visualization_image:
            viz_path = st.session_state.visualization_image
            if os.path.exists(viz_path):
                st.subheader("Current Visualization")
                try:
                    image = Image.open(viz_path)
                    st.image(image, caption="DALL-E Generated Visualization", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying visualization: {e}")
            else:
                st.warning("Visualization file not found. It may have been moved or deleted.")
                # Clean up the session state
                st.session_state.visualization_image = None
        
        # Adapt button
        if st.button("✨ Adapt Content", type="primary", use_container_width=True, disabled=not assistant):
            current_text = st.session_state.input_text_area_content
            if not current_text:
                st.warning("Please enter or generate some content first.")
            else:
                is_new = (not st.session_state.current_content_id or 
                          current_text != st.session_state.original_text)
                
                # Save new content if needed
                if is_new:
                    with st.spinner("Analyzing and storing content..."):
                        st.session_state.original_text = current_text
                        st.session_state.structured_description = assistant.structure_content_description(current_text)
                        title = (st.session_state.topic_input or "Pasted")[:50]
                        source = 'generated' if st.session_state.topic_input else 'pasted'
                        st.session_state.current_content_id = db.store_content_piece(
                            title, 
                            current_text, 
                            st.session_state.structured_description, 
                            source, 
                            st.session_state.topic_input
                        )
                        skills = assistant.identify_content_skills(current_text)
                        if skills:
                            db.map_content_skills(st.session_state.current_content_id, skills)
                        st.session_state.start_time = time.time()
                
                # Generate adaptations
                with st.spinner("Generating adaptations..."):
                    adaptations = asyncio.run(assistant.apply_adaptations_async(
                        current_text, 
                        st.session_state.current_profile
                    ))
                    st.session_state.current_adaptations = adaptations
                    
                    # Log interaction
                    if st.session_state.current_content_id:
                        t_spent = int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0
                        db.store_interaction(
                            st.session_state.user_id, 
                            st.session_state.current_content_id, 
                            'adapt_view', 
                            t_spent
                        )
                        st.session_state.start_time = time.time()
                    
                    st.success("Adaptations ready!")
                    st.rerun()
    
    # Output column
    with col2:
        st.header("Adapted Content")
        adaptations = st.session_state.current_adaptations
        original_text = st.session_state.original_text
        
        if not adaptations and not original_text:
            st.info("Enter content and click 'Adapt Content' to see adaptations here.")
        elif not adaptations and original_text:
            # Show original + listen if no adaptations yet
            with st.expander("Original Text", expanded=True):
                st.markdown(original_text)
                # TTS Button for Original
                if is_tts_available() and st.button("Listen 🎧##Original", key="tts_btn_orig_only"):
                    audio_data = generate_tts_audio(original_text)
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                    else:
                        st.warning("Audio generation failed.")
            st.info("Click 'Adapt Content' to generate tailored versions.")
        elif adaptations:
            # Show adaptations + original + TTS
            with st.expander("Original Text", expanded=False):
                st.markdown(original_text)
                if is_tts_available() and st.button("Listen 🎧##Original", key="tts_btn_orig_adap"):
                    audio_data = generate_tts_audio(original_text)
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                    else:
                        st.warning("Audio generation failed.")
            
            # Adaptation Display + TTS
            display_count = 0
            
            # Simplified for dyslexia
            if "simplified_dyslexia" in adaptations:
                display_count += 1
                st.subheader("Simplified")
                text = adaptations["simplified_dyslexia"]
                st.markdown(text)
                if is_tts_available() and st.button("Listen 🎧##Simplified", key="tts_btn_simp"):
                    audio_data = generate_tts_audio(text)
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                    else:
                        st.warning("Audio generation failed.")
            
            # Syllable breakdown
            if "syllable_breakdown" in adaptations:
                display_count += 1
                st.subheader("Syllables")
                st.text(adaptations["syllable_breakdown"])
            
            # Dyslexia UI notes
            if "dyslexia_ui_notes" in adaptations:
                display_count += 1
                st.info(f"Suggestions: {adaptations['dyslexia_ui_notes']}")
            
            # Math visualization (DALL-E version)
            if "math_visualization_image" in adaptations and os.path.exists(adaptations["math_visualization_image"]):
                display_count += 1
                st.subheader("Math Visualization")
                
                # Show explanation text if available
                if "math_visualization_text" in adaptations:
                    st.markdown(adaptations["math_visualization_text"])
                
                # Display the image
                try:
                    image = Image.open(adaptations["math_visualization_image"])
                    st.image(image, caption="DALL-E Math Visualization", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying math visualization: {e}")
            # Fallback to traditional math visualization if DALL-E version not available
            elif "math_visualization" in adaptations:
                display_count += 1
                st.subheader("Math Visualization")
                content = adaptations["math_visualization"]
                mc = extract_mermaid_code(content)
                exp = re.sub(r"```mermaid.*?```", "", content, flags=re.DOTALL|re.I).strip() if mc else content
                
                if exp:
                    st.markdown(exp)
                if mc:
                    try:
                        from ui.rendering import render_mermaid
                        render_mermaid(mc)
                    except ImportError:
                        st.code(mc, language="mermaid")
                elif "do not include" not in content.lower():
                    st.caption("(No diagram needed)")
            
            # Concept visualization (DALL-E for visual learners)
            if "concept_visualization_image" in adaptations and os.path.exists(adaptations["concept_visualization_image"]):
                display_count += 1
                st.subheader("Visual Concept Representation")
                
                # Show concept text if available
                if "concept_visualization_text" in adaptations:
                    st.markdown(f"**Visualizing:** {adaptations['concept_visualization_text']}")
                
                # Display the image
                try:
                    image = Image.open(adaptations["concept_visualization_image"])
                    st.image(image, caption="DALL-E Concept Visualization", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying concept visualization: {e}")
            
            # Instruction visualization (DALL-E version)
            if "instruction_visualization_image" in adaptations and os.path.exists(adaptations["instruction_visualization_image"]):
                display_count += 1
                st.subheader("Instructions Visualization")
                
                # Show instruction text if available
                if "instruction_visualization_text" in adaptations:
                    st.markdown(adaptations["instruction_visualization_text"])
                
                # Display the image
                try:
                    image = Image.open(adaptations["instruction_visualization_image"])
                    st.image(image, caption="DALL-E Instruction Visualization", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying instruction visualization: {e}")
            # Fallback to traditional instruction visualization if DALL-E version not available
            elif "instruction_visualization" in adaptations:
                display_count += 1
                st.subheader("Instruction Visualization")
                content = adaptations["instruction_visualization"]
                mc = extract_mermaid_code(content)
                exp = re.sub(r"```mermaid.*?```", "", content, flags=re.DOTALL|re.I).strip() if mc else content
                
                if exp and exp != content:
                    st.markdown(exp)
                elif not mc:
                    st.markdown(content)
                
                if mc:
                    try:
                        from ui.rendering import render_mermaid
                        render_mermaid(mc)
                    except ImportError:
                        st.code(mc, language="mermaid")
                elif "do not generate" not in content.lower():
                    st.caption("(No diagram needed)")
            
            # Chunked content for ADHD
            if "chunked_adhd" in adaptations:
                display_count += 1
                st.subheader("Chunked")
                chunks = adaptations["chunked_adhd"]
                if isinstance(chunks, list):
                    for i, chunk in enumerate(chunks):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.markdown(chunk)
                        if is_tts_available() and st.button(f"Listen 🎧##Chunk{i}", key=f"tts_btn_chunk_{i}"):
                            audio = generate_tts_audio(chunk)
                            if audio:
                                st.audio(audio, format='audio/mp3', key=f"audio_chunk_{i}")
                            else:
                                st.warning("Audio generation failed.")
                        st.markdown("---")
                else:
                    st.warning("Chunk parsing failed")
                    st.text(chunks)
            elif "chunked_adhd_raw" in adaptations:
                display_count += 1
                st.subheader("Chunked (Raw)")
                st.text(adaptations["chunked_adhd_raw"])
            
            # Dysgraphia support
            if "dysgraphia_support" in adaptations:
                display_count += 1
                st.info(f"Suggestions: {adaptations['dysgraphia_support']}")
            
            # Auditory processing support
            if "ap_support" in adaptations:
                display_count += 1
                st.info(f"Suggestions: {adaptations['ap_support']}")
            
            # Reading/Writing summary
            if "summary_rw" in adaptations:
                display_count += 1
                st.subheader("Summary")
                text = adaptations["summary_rw"]
                st.markdown(text)
                if is_tts_available() and st.button("Listen 🎧##Summary", key="tts_btn_summ"):
                    audio_data = generate_tts_audio(text)
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                    else:
                        st.warning("Audio generation failed.")
            
            # Learning style notes
            for key in ["visual_learner_note", "auditory_learner_note", "kinesthetic_learner_note"]:
                if key in adaptations:
                    display_count += 1
                    st.info(adaptations[key])
            
            if display_count == 0:
                st.info("No specific adaptations were generated for the current profile.")
            
            # Feedback Section
            st.markdown("---")
            st.subheader("Feedback")
            if not st.session_state.current_content_id:
                st.warning("Adapt content first to provide feedback.")
            else:
                with st.form("feedback_form"):
                    rating = st.slider("Helpfulness:", 1, 5, 3, key="fb_rating")
                    comment = st.text_area("Comments:", key="fb_comment")
                    submitted = st.form_submit_button("Submit Feedback")
                
                if submitted:
                    t_spent = int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0
                    db.store_interaction(
                        st.session_state.user_id,
                        st.session_state.current_content_id,
                        'feedback',
                        t_spent,
                        feedback_rating=rating,
                        feedback_comment=comment
                    )
                    st.success("Feedback submitted! Your skills have been updated.")
                    st.session_state.start_time = time.time()