import fitz  # PyMuPDF library is imported as fitz
import os
import streamlit as st

def extract_text_from_pdf(pdf_path: str) -> str | None:
    """
    Extracts all text content from a given PDF file.

    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        A string containing the extracted text from all pages,
        or None if the file cannot be processed or doesn't exist.
    """
    if not os.path.exists(pdf_path):
        st.error(f"Error: File not found at '{pdf_path}'")
        return None
    if not pdf_path.lower().endswith(".pdf"):
        st.error(f"Error: File '{os.path.basename(pdf_path)}' does not appear to be a PDF.")
        return None

    all_text = ""
    doc = None # Initialize doc to None for finally block safety
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)

        # Iterate through each page
        with st.spinner(f"Processing {doc.page_count} pages from '{os.path.basename(pdf_path)}'..."):
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text("text") # Extract text from the page
                all_text += page_text
                # You could add page breaks if needed:
                # if page_num < doc.page_count - 1:
                #     all_text += "\n\n--- Page Break ---\n\n"

        return all_text

    except Exception as e:
        # Provide more specific error context if possible
        st.error(f"Error processing PDF '{os.path.basename(pdf_path)}': {e}")
        return None
    finally:
        # Ensure the document is closed even if an error occurs
        if doc:
            try:
                doc.close()
            except Exception as close_err:
                # Log or print error during closing if necessary, but don't prevent return
                st.warning(f"Warning: Error closing PDF document: {close_err}")
                
def extract_text_from_uploaded_pdf(uploaded_file) -> str | None:
    """
    Extracts text from a PDF file uploaded through Streamlit.
    
    Args:
        uploaded_file: The Streamlit UploadedFile object
        
    Returns:
        A string containing the extracted text or None on failure
    """
    if not uploaded_file.name.lower().endswith('.pdf'):
        st.error(f"Error: '{uploaded_file.name}' does not appear to be a PDF.")
        return None
        
    try:
        # Create a temporary file to save the uploaded content
        with st.spinner(f"Processing uploaded PDF: {uploaded_file.name}..."):
            # Save uploaded file to a temporary file
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract text using the existing function
            text = extract_text_from_pdf(temp_file_path)
            
            # Clean up the temporary file
            try:
                os.remove(temp_file_path)
            except Exception as e:
                st.warning(f"Warning: Could not remove temporary file: {e}")
                
            return text
            
    except Exception as e:
        st.error(f"Error processing uploaded PDF: {e}")
        return None