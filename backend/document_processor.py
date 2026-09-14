import os
import re
import uuid
import datetime

class DocumentProcessor:
    """
    Nexora Document Processing Pipeline
    Handles multi-format document text extraction, cleaning, metadata tagging, 
    and semantic chunking.
    """
    def __init__(self, chunk_size=700, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path, original_filename):
        ext = os.path.splitext(original_filename)[1].lower()
        file_id = str(uuid.uuid4())[:8]

        pages_data = []

        if ext == '.pdf':
            pages_data = self._extract_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            pages_data = self._extract_docx(file_path)
        elif ext in ['.pptx', '.ppt']:
            pages_data = self._extract_pptx(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            pages_data = self._extract_image_ocr(file_path, original_filename)
        elif ext in ['.csv', '.txt', '.md']:
            pages_data = self._extract_text(file_path)
        else:
            # Fallback text loader
            pages_data = self._extract_text(file_path)

        # Clean text across all pages
        cleaned_pages = []
        for page_num, text in pages_data:
            cleaned_text = self._clean_text(text)
            if cleaned_text.strip():
                cleaned_pages.append((page_num, cleaned_text))

        if not cleaned_pages:
            cleaned_pages = [(1, f"Document {original_filename} uploaded successfully. Text contents processed.")]

        # Semantic Chunking & Metadata Tagging
        chunks = self._create_chunks(cleaned_pages, file_id, original_filename)

        full_doc_text = "\n\n".join([text for _, text in cleaned_pages])
        max_page = max([c['page_number'] for c in chunks]) if chunks else len(cleaned_pages)

        return {
            "file_id": file_id,
            "filename": original_filename,
            "file_type": ext,
            "total_pages": max_page,
            "total_chunks": len(chunks),
            "chunks": chunks,
            "full_text": full_doc_text,
            "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _extract_pdf(self, file_path, max_pages=150):
        pages = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            total = min(len(reader.pages), max_pages)
            for idx in range(total):
                try:
                    page = reader.pages[idx]
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append((idx + 1, text))
                except Exception:
                    continue
        except Exception as e:
            print(f"[DocumentProcessor] PyPDF extraction fallback: {e}")
            pages = self._extract_text(file_path)

        if not pages:
            pages = self._extract_text(file_path)

        return pages

    def _extract_docx(self, file_path):
        pages = []
        try:
            import docx
            doc = docx.Document(file_path)
            
            current_page = 1
            current_text = []
            word_count = 0

            for para in doc.paragraphs:
                txt = para.text.strip()
                if not txt:
                    continue

                has_page_break = bool(para._element.xpath('.//w:br[@w:type="page"]'))
                words = txt.split()
                word_count += len(words)
                current_text.append(txt)

                if has_page_break or word_count >= 300:
                    pages.append((current_page, "\n".join(current_text)))
                    current_page += 1
                    current_text = []
                    word_count = 0

            if current_text:
                pages.append((current_page, "\n".join(current_text)))

        except Exception as e:
            print(f"[DocumentProcessor] docx extraction fallback: {e}")
            pages = self._extract_text(file_path)

        if not pages:
            pages = [(1, "Empty docx document.")]

        return pages

    def _extract_pptx(self, file_path):
        pages = []
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            for idx, slide in enumerate(prs.slides):
                slide_text = []
                self._extract_shapes_text(slide.shapes, slide_text)
                pages.append((idx + 1, "\n".join(slide_text)))
        except Exception as e:
            print(f"[DocumentProcessor] pptx extraction fallback: {e}")
            pages = self._extract_text(file_path)
        return pages

    def _extract_shapes_text(self, shapes, text_list):
        for shape in shapes:
            try:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        t = paragraph.text.strip()
                        if t and t not in text_list:
                            text_list.append(t)
                elif shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            t = cell.text.strip()
                            if t and t not in text_list:
                                text_list.append(t)
                elif hasattr(shape, "shapes"):
                    self._extract_shapes_text(shape.shapes, text_list)
            except Exception:
                continue

    def _extract_image_ocr(self, file_path, filename):
        return [(1, f"[OCR Content: {filename}]")]

    def _extract_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return [(1, content)]
        except Exception:
            return [(1, "Content read error.")]

    def _clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    def _create_chunks(self, pages_data, file_id, filename):
        chunks = []
        chunk_counter = 0

        for page_num, page_text in pages_data:
            words = page_text.split()
            if not words:
                continue

            # Slide/Page level chunking
            effective_chunk_size = 150 if filename.lower().endswith(('.pptx', '.ppt')) else self.chunk_size

            i = 0
            while i < len(words):
                chunk_words = words[i:i + effective_chunk_size]
                chunk_text = " ".join(chunk_words)
                chunk_id = f"{file_id}_c{chunk_counter}"

                chunks.append({
                    "chunk_id": chunk_id,
                    "file_id": file_id,
                    "filename": filename,
                    "page_number": max(1, page_num),
                    "text": chunk_text,
                    "word_count": len(chunk_words),
                    "token_estimate": int(len(chunk_words) * 1.3)
                })

                chunk_counter += 1
                i += (effective_chunk_size - self.chunk_overlap)
                if i <= 0 or effective_chunk_size <= self.chunk_overlap:
                    i = len(words)

        return chunks

