#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
from flask import Flask,request,jsonify
from PIL import Image
import os
import pytesseract
from groq import Groq
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

os.environ['GROQ_API_KEY'] = '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'
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise EnvironmentError("Please set the groq key as enviroment variable")

client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)

CATEGORY_MAPPING = {
    "CN": "Sem - 3",
    "DMGT": "Sem - 3",
    "DSA": "Sem - 3",
    "CAO": "Sem - 3",
    "MPMC": "Sem - 3",
    "DSD": "Sem - 2",
    "EE": "Sem - 2",
}

def sanitize_output(input_string):
    
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return sanitized

@app.route('/upload',methods = ['POST'])
def classify():
    try:
        print("Received request")
        if 'file' not in request.files:
            print("No file part")
            return 'No file part', 400
        file = request.files['file']
        file_path = "temp.jpg"
        file.save(file_path)

        ex_text = extract_text_from_image(file_path)
        if not ex_text.strip():
            return jsonify({"error":"No text could be found in the image."})
        
        subcategory = classify_question_paper(ex_text)
        subcat = sanitize_output(subcategory)
        main_category = CATEGORY_MAPPING.get(subcat, "Others")

        if subcategory not in CATEGORY_MAPPING:
            CATEGORY_MAPPING[subcategory] = "Others"

        return jsonify({"subcategory":subcat,"main_category":main_category})
    except Exception as e:
        return jsonify({"error":str(e)}),500
    
def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(img)
        #print(extracted_text)
        return extracted_text
    except Exception as e:
        raise ValueError(f"Error extracting text: {e}")
    
def classify_question_paper(text):
    try:
        prompt = (
            f"Question paper: {text}"
            "Find out the subject of the following Question paper:"
            "Here are some of the subjects given as examples"
            "CN(computer networks)"
            "DSA(Data structures and algorithms)"
            "DMGT(Discreet mathematics and graph theory)"
            "CAO(computer architecture and organisation)"
            "MPMC(Micro processors and micro controllers)"
            "DSD(Digital system design)"
            "EE(electrical and electronics)"
            "give subject name in 1 word abbrevation with no bold or any other effects on them"
            "please give the answer strictly in only 1 word"
            "only 1 WORD ANSWER IS REQUIRED"
            "Examples:"
            "question paper is computer networks-> answer: CN"
            "question paper is internet of things-> answer: IOT"
            "question paper is human-computer interaction-> answer: HCI"
            "question paper is image processing-> anwer: IP"
            
        )
        response = client.chat.completions.create(
            messages=[
                {"role":"user","content":prompt}
            ],
            temperature=0,
            model="llama-3.1-8b-instant"
        )

        category = response.choices[0].message.content.strip()
        return category
    except Exception as e:
        raise RuntimeError(f"Error classifying question paper: {e}")
    
if __name__ == '__main__':
    app.run(debug=True)
