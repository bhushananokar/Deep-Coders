import fitz  # PyMuPDF library is imported as fitz
import os

def extract_text_from_pdf(pdf_path: str) -> str | None:
    """
    Extracts all text content from a given PDF file.

    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        A string containing the extracted text from all pages,
        or None if the file cannot be processed or doesn't exist.
        Prints error messages to the console in case of issues.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at '{pdf_path}'")
        return None
    if not pdf_path.lower().endswith(".pdf"):
        print(f"Error: File '{os.path.basename(pdf_path)}' does not appear to be a PDF.")
        return None

    all_text = ""
    doc = None # Initialize doc to None for finally block safety
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)

        # Iterate through each page
        print(f"Processing {doc.page_count} pages from '{os.path.basename(pdf_path)}'...")
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text("text") # Extract text from the page
            all_text += page_text
            # You could add page breaks if needed:
            # if page_num < doc.page_count - 1:
            #     all_text += "\n\n--- Page Break ---\n\n"

        print("Text extraction complete.")
        return all_text

    except Exception as e:
        # Provide more specific error context if possible
        print(f"Error processing PDF '{os.path.basename(pdf_path)}': {e}")
        # Consider logging the full traceback here for complex issues
        # import traceback
        # traceback.print_exc()
        return None
    finally:
        # Ensure the document is closed even if an error occurs
        if doc:
            try:
                doc.close()
            except Exception as close_err:
                # Log or print error during closing if necessary, but don't prevent return
                print(f"Warning: Error closing PDF document: {close_err}")


# --- Main execution block ---
if __name__ == "__main__":
    # --- !!! SET THE PATH TO YOUR PDF FILE HERE !!! ---
    # Option 1: Windows path (use r"..." raw string or double backslashes \\)
    pdf_file_to_process = r"C:\Users\Bhushan\Downloads\Content Beyond Syllabus.pdf"
    # pdf_file_to_process = "C:\\path\\to\\your\\document.pdf"

    # Option 2: Linux/macOS path
    # pdf_file_to_process = "/home/user/documents/report.pdf"

    # --- End of configuration ---

    print(f"Attempting to extract text from: {pdf_file_to_process}")

    # Call the extraction function with the hardcoded path
    extracted_content = extract_text_from_pdf(pdf_file_to_process)

    # Print the extracted content if successful
    if extracted_content is not None:
        print("\n--- Extracted PDF Content ---")
        print(extracted_content)

        # --- Optional: Save the extracted text to a file ---
        # output_filename = os.path.splitext(pdf_file_to_process)[0] + "_extracted.txt"
        # try:
        #     with open(output_filename, "w", encoding="utf-8") as f:
        #         f.write(extracted_content)
        #     print(f"\nExtracted text also saved to: {output_filename}")
        # except IOError as e:
        #     print(f"\nError: Could not save extracted text to file '{output_filename}': {e}")
        # except Exception as e:
        #      print(f"\nAn unexpected error occurred while saving the file: {e}")
        # --- End of Optional Save ---

    else:
        print("\nExtraction failed or the PDF might not contain extractable text.")