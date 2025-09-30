import os
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

# 计算文件夹下所有pdf总页数
def count_total_pdf_pages(directory: str) -> int:
    total_pages = 0
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' not found")
        return 0

    print(f"Scanning directory: {directory}...")
    for filename in os.listdir(directory):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    num_pages = len(reader.pages)
                    total_pages += num_pages
                    print(f"Processed '{filename}': {num_pages} pages.")
            except PdfReadError:
                print(f"Skipping corrupted or unreadable PDF: {filename}")
            except Exception as e:
                print(f"An unexpected error occurred with file {filename}: {e}")
    
    print(f"Scan complete. Total pages found: {total_pages}")
    return total_pages

if __name__ == '__main__':
    current_directory = os.path.dirname(os.path.abspath(__file__))
    reports_folder = os.path.join(current_directory, 'reports')
    
    if not os.path.exists(reports_folder):
        os.makedirs(reports_folder)
        print(f"Created a dummy '{reports_folder}' directory.")

    total_pages_count = count_total_pdf_pages(reports_folder)
    print(f"\nGrand total of pages in '{reports_folder}': {total_pages_count}")
