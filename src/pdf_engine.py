from pathlib import Path
from pypdf import PdfReader, PdfWriter


def get_pdf_page_count(file_path: str) -> int:
    reader = PdfReader(file_path)
    return len(reader.pages)


def merge_pdfs(file_paths: list[str], output_path: str) -> None:
    writer = PdfWriter()
    for path in file_paths:
        writer.append(path)
    with open(output_path, "wb") as f:
        writer.write(f)


def split_pdf(file_path: str, start_page: int, end_page: int, output_path: str) -> None:
    reader = PdfReader(file_path)
    total = len(reader.pages)
    if start_page < 1 or end_page > total or start_page > end_page:
        raise ValueError("Invalid page range")

    writer = PdfWriter()
    for page_idx in range(start_page - 1, end_page):
        writer.add_page(reader.pages[page_idx])

    with open(output_path, "wb") as f:
        writer.write(f)


def rotate_pdf(file_path: str, angle: int, output_path: str) -> None:
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


def optimize_and_protect_pdf(
    file_path: str, output_path: str, compress: bool = True, password: str = ""
) -> tuple[int, int]:
    orig_kb = max(1, round(Path(file_path).stat().st_size / 1024))
    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    if compress:
        for page in writer.pages:
            page.compress_content_streams()
        writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)

    if password.strip():
        writer.encrypt(password.strip())

    with open(output_path, "wb") as f:
        writer.write(f)

    new_kb = max(1, round(Path(output_path).stat().st_size / 1024))
    return orig_kb, new_kb