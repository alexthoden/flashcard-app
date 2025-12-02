import re
import PyPDF2
import random

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file."""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def parse_questions(text):
    """Parse questions and answers into flashcards."""
    flashcards = []
    
    # Regex pattern to capture question blocks
    pattern = re.compile(
        r"Question\s*(\d+):\s*(.*?)\s*A\)(.*?)\s*B\)(.*?)\s*C\)(.*?)\s*D\)(.*?)\s*Correct\s*answer:\s*(\w)",
        re.DOTALL
    )
    
    for match in pattern.finditer(text):
        q_num = match.group(1).strip()
        question = match.group(2).strip().replace("	", " ")
        options = {
            "A": match.group(3).strip().replace("	", " "),
            "B": match.group(4).strip().replace("	", " "),
            "C": match.group(5).strip().replace("	", " "),
            "D": match.group(6).strip().replace("	", " ")
        }
        correct = match.group(7).strip()
        
        flashcards.append({
            "question_number": q_num,
            "question": question,
            "options": options,
            "correct_answer": correct
        })
    
    return flashcards

def run_quiz(flashcards):
    remaining = flashcards.copy()
    random.shuffle(remaining)

    while remaining:
        card = remaining.pop(0)  # take one question
        print(f"\nQ{card['question_number']}: {card['question']}")
        for opt, val in card['options'].items():
            print(f"  {opt}) {val}")

        # Get user input
        answer = input("Your answer (a/b/c/d): ").strip().upper()

        # Validate
        if answer == card['correct_answer']:
            print("✅ Correct!\n")
            # Do not re-add the card (removes from pool)
        else:
            print(f"❌ Incorrect. Correct answer: {card['correct_answer']}\n")
            # Put back at the end of the list to retry later
            remaining.append(card)

    print("🎉 All questions answered correctly!")

def main():
    pdf_path = "questions.pdf"  # replace with your PDF file path
    text = extract_text_from_pdf(pdf_path)
    flashcards = parse_questions(text)
    run_quiz(flashcards)

if __name__ == "__main__":
    main()	