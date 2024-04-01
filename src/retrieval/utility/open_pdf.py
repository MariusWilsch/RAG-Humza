import webbrowser

def open_pdf_at_page(pdf_path, page_number):
    # Construct the URL with the PDF path and page parameter
    url = f"file://{pdf_path}#page={page_number}"

    # Open the PDF in the user's default browser at the specified page
    webbrowser.open(url)
