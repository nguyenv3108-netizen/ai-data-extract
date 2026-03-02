from flask import Flask, render_template, request
import json
import PyPDF2
from openai import OpenAI

from keys import OPENAI_API_KEY

# Initialize Flask
app = Flask(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

EXTRACTION_PROMPT = """
You are a financial assistant that extracts structured data from invoices.

Extract the following fields from the pdf:
    {
        "vendor_name": "{vendor name}",
        "invoice_number: "{invoice number}",
        "start_date": "{start date}",
        "end_date": "{end date}",
        "total_due: "{total due}"
    }
    
Use the following format for the dates: MM/DD/YYYY.
Ensure the total amount has a $ sign, and NO paranthesis. If there is no sign in the data assume that it is USD and use $ sign.

Always respond with **valid JSON ONLY**, no extra text, or a 'json' text in the string.
"""

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


@app.route("/", methods=["GET", "POST"])
def index():
    extracted_data = None
    raw_text = None
    if request.method == "POST":
        pdf_file = request.files["invoice"]
        if pdf_file:
            raw_text = extract_text_from_pdf(pdf_file)

            # Call GPT-4o-mini to structure the text
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": EXTRACTION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": raw_text
                    }
                ],
                temperature=0
            )

            print(response.choices[0].message.content)
            try:
                extracted_data = json.loads(response.choices[0].message.content)
            except Exception as e:
                extracted_data = {"error": f"Failed to parse JSON: {str(e)}"}

            # extracted_data = json.loads(response.choices[0].message.content)
            print("extracted data")
            print(extracted_data)

    return render_template("index.html", data=extracted_data, text=raw_text)


if __name__ == "__main__":
    app.run(debug=True)