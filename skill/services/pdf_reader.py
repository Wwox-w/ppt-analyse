from PyPDF2 import PdfReader

def read_pdf(file):
    reader = PdfReader(file)
    contents = []

    for page in reader.pages:
        text = page.extract_text()
        contents.append(text if text else "")

    return contents