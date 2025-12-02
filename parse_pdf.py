# parse_pdf.py
import re
import json
import PyPDF2

PDF_PATH = "questions.pdf"
OUTPUT_FILE = "questions.json"

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text

def parse_questions(text):
    flashcards = []
    pattern = re.compile(
        r"Question\s*(\d+):\s*(.*?)\s*A\)(.*?)\s*B\)(.*?)\s*C\)(.*?)\s*D\)(.*?)\s*Correct\s*answer:\s*(\w)",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        q_num = match.group(1).strip()
        question = match.group(2).strip().replace("\t", " ")
        options = {
            "A": match.group(3).strip().replace("\t", " "),
            "B": match.group(4).strip().replace("\t", " "),
            "C": match.group(5).strip().replace("\t", " "),
            "D": match.group(6).strip().replace("\t", " "),
        }
        correct = match.group(7).strip().upper()
        flashcards.append({
            "question_number": q_num,
            "question": question,
            "options": options,
            "correct_answer": correct,
        })
    return flashcards

def main():
    text = extract_text_from_pdf(PDF_PATH)
    flashcards = parse_questions(text)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(flashcards, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(flashcards)} questions to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()