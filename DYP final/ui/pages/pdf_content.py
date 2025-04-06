import streamlit as st
import os
import time
from utils.pdf_extractor import extract_text_from_uploaded_pdf

def render(db, assistant, reset_content_state):
    """Render the PDF content extraction page."""
    st.title("📄 PDF Content Extractor")
    
    if not assistant:
        st.warning("API key required. Enter a valid API key in the sidebar to use AI features.")
    
    st.markdown("""
    Upload a PDF document to extract its text content. The extracted text can then be adapted 
    to match your learning style and needs using the AdaptLearn AI features.
    """)
    
    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"], key="pdf_uploader")
    
    # Store extracted text in session state to persist between reruns
    if "pdf_extracted_text" not in st.session_state:
        st.session_state.pdf_extracted_text = None
    
    # Handle extract button and store results
    if uploaded_file is not None:
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"Selected file: **{uploaded_file.name}**")
        
        with col2:
            extract_button = st.button("Extract Text", key="extract_btn", use_container_width=True)
        
        if extract_button:
            # Extract text from the PDF
            extracted_text = extract_text_from_uploaded_pdf(uploaded_file)
            
            if extracted_text:
                st.session_state.pdf_extracted_text = extracted_text
                st.session_state.pdf_filename = uploaded_file.name
                st.success(f"Successfully extracted text from {uploaded_file.name}!")
    
    # Display and process extracted text if available
    if st.session_state.pdf_extracted_text:
        # Preview the extracted text
        with st.expander("Preview Extracted Text", expanded=True):
            st.text_area("Extracted Content", st.session_state.pdf_extracted_text, height=300)
        
        # Options for what to do with the text
        st.markdown("---")
        st.subheader("What would you like to do with this content?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Adapt Content", key="adapt_content_btn", use_container_width=True):
                # First reset content state to clear any previous content
                reset_content_state()
                
                # Set up session state variables for adapt_content page
                st.session_state.input_text_area_content = st.session_state.pdf_extracted_text
                st.session_state.original_text = st.session_state.pdf_extracted_text
                
                # Use filename without extension as topic
                file_basename = os.path.splitext(st.session_state.pdf_filename)[0]
                st.session_state.topic_input = file_basename
                
                # Store content in database
                struct_desc = assistant.structure_content_description(st.session_state.pdf_extracted_text) if assistant else ""
                title = f"PDF: {file_basename}"
                
                content_id = db.store_content_piece(
                    title, 
                    st.session_state.pdf_extracted_text, 
                    struct_desc, 
                    'pdf', 
                    file_basename
                )
                
                st.session_state.current_content_id = content_id
                
                # Identify skills if assistant is available
                if assistant:
                    skills = assistant.identify_content_skills(st.session_state.pdf_extracted_text)
                    if skills:
                        db.map_content_skills(content_id, skills)
                        
                st.session_state.start_time = time.time()
                
                # Change page and force rerun to refresh the UI
                st.session_state.page = "adapt_content"
                st.rerun()
        
        with col2:
            quiz_button_disabled = not assistant
            quiz_button_help = "API key required for quiz generation" if quiz_button_disabled else None
            
            if st.button("Generate Quiz", key="gen_quiz_btn", use_container_width=True, disabled=quiz_button_disabled, help=quiz_button_help):
                # Prepare for quiz generation
                file_basename = os.path.splitext(st.session_state.pdf_filename)[0]
                st.session_state.quiz_from_pdf = True
                st.session_state.quiz_pdf_topic = file_basename
                
                # Set a flag to show quiz form
                st.session_state.show_quiz_form = True
                st.rerun()
        
        # Show quiz form if requested
        if st.session_state.get("show_quiz_form", False):
            st.markdown("---")
            st.subheader("Generate Quiz from PDF Content")
            
            with st.form("quiz_params_form"):
                quiz_topic = st.text_input("Quiz Topic", value=st.session_state.get("quiz_pdf_topic", ""))
                col1, col2 = st.columns(2)
                with col1:
                    difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)
                with col2:
                    num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5, step=1)
                
                generate_quiz = st.form_submit_button("Generate Quiz")
            
            if generate_quiz:
                with st.spinner("Generating quiz based on PDF content..."):
                    # Generate the quiz
                    quiz_id, message = assistant.generate_quiz(
                        st.session_state.user_id,
                        quiz_topic,
                        difficulty, 
                        num_questions
                    )
                    
                    if quiz_id:
                        st.success("Quiz generated successfully!")
                        
                        # Start the quiz attempt
                        attempt_id = db.start_quiz_attempt(quiz_id, st.session_state.user_id)
                        
                        if attempt_id:
                            # Set up quiz session state
                            st.session_state.current_quiz_id = quiz_id
                            st.session_state.current_attempt_id = attempt_id
                            st.session_state.current_question_idx = 0
                            st.session_state.question_start_time = time.time()
                            st.session_state.quiz_answers = {}
                            
                            # Clean up PDF-specific session variables
                            st.session_state.pop("show_quiz_form", None)
                            st.session_state.pop("quiz_from_pdf", None)
                            st.session_state.pop("quiz_pdf_topic", None)
                            
                            # Redirect to quiz page
                            st.session_state.page = "quiz"
                            st.rerun()
                        else:
                            st.error("Failed to start quiz attempt.")
                    else:
                        st.error(f"Failed to generate quiz: {message}")
        
        # Add a text area to edit the extracted content
        st.markdown("---")
        st.subheader("Edit Extracted Content")
        
        edited_text = st.text_area("Edit the extracted text if needed:", 
                                 value=st.session_state.pdf_extracted_text, 
                                 height=400,
                                 key="edited_pdf_text")
        
        if edited_text != st.session_state.pdf_extracted_text and st.button("Use Edited Text", key="use_edited_btn"):
            st.session_state.pdf_extracted_text = edited_text
            st.success("Text updated successfully!")
            st.rerun()
    elif uploaded_file is not None and st.session_state.pdf_extracted_text is None:
        # This means extraction hasn't happened yet or failed
        pass
    else:
        # Show a placeholder or instructions when no file is uploaded
        st.info("Please upload a PDF document to extract its content.")
        
        # Optionally, show some tips or examples
        with st.expander("Tips for best results"):
            st.markdown("""
            - For best results, upload PDFs with actual text content (not scanned images)
            - The extraction process works on text that can be selected in the PDF
            - If your PDF is scanned, consider using OCR software to convert it first
            - Large PDFs may take longer to process
            """)
    
    # Add a section about handling academic PDFs
    st.markdown("---")
    with st.expander("About PDF Content Extraction"):
        st.markdown("""
        ### How it works
        
        The PDF extraction tool uses PyMuPDF to extract text content from your PDF documents. This works best with:
        
        - Digitally created PDFs (not scanned documents)
        - PDFs with selectable text content
        - Non-encrypted documents
        
        ### Academic Use
        
        This tool is especially useful for:
        
        - Extracting content from academic papers for study
        - Converting textbook content to adaptable formats
        - Breaking down complex material into smaller, more accessible segments
        - Creating quizzes based on course material
        
        ### Privacy Notice
        
        Your uploaded documents are processed locally and are not stored permanently unless you choose to adapt or use the content.
        """)