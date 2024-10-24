import os
import pandas as pd
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from pdfrw import PdfReader, PdfWriter, PdfDict
import zipfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Setze ein Geheimnis für die Sitzungsverwaltung

# Directory and file paths
TEMPLATE_DIR = "document_templates/"
OUTPUT_DIR = "output/"
EXCEL_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "data_template.xlsx")

# Helper function to create output directory
def create_output_directory():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# Function to read PDF fields
def get_pdf_fields(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF template not found at {pdf_path}")
    
    template_pdf = PdfReader(pdf_path)
    fields = {}
    for page in template_pdf.pages:
        annotations = page.Annots
        if annotations:
            for annotation in annotations:
                field_name = annotation.T
                if field_name:
                    fields[field_name[1:-1]] = None  # Remove brackets
    return fields

# Function to create contracts from Excel
def create_contracts_from_excel(excel_path, pdf_template_path):
    create_output_directory()  # Ensure output directory exists
    
    # Ensure the uploaded file exists
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found at {excel_path}")
    
    df = pd.read_excel(excel_path)
    pdf_files = []  # To keep track of generated PDFs

    pdf_fields = get_pdf_fields(pdf_template_path)
    
    for index, row in df.iterrows():
        if row.isnull().all():
            continue  # Skip empty rows

        filled_fields = {pdf_field: str(row[pdf_field]) for pdf_field in pdf_fields if pdf_field in row}
        company_name = row["###company###"]
        output_pdf_name = f"{company_name} Antrag SGB Vertrag.pdf"
        output_pdf_path = os.path.join(OUTPUT_DIR, output_pdf_name)

        # Generate PDF
        generate_pdf(filled_fields, pdf_template_path, output_pdf_path)
        pdf_files.append(output_pdf_name)

    return pdf_files

# Function to generate PDF
def generate_pdf(field_data, template_path, output_pdf_path):
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page in reader.pages:
        annotations = page.Annots
        if annotations:
            for annotation in annotations:
                field_name = annotation.T
                if field_name:
                    field_name_str = field_name[1:-1]  # Remove brackets
                    if field_name_str in field_data:
                        annotation.update(PdfDict(V='{}'.format(field_data[field_name_str])))

        writer.addpage(page)

    with open(output_pdf_path, "wb") as output_pdf_file:
        writer.write(output_pdf_file)

# Function to create a zip file
def create_zip(pdf_files):
    zip_filename = os.path.join(OUTPUT_DIR, "contracts.zip")
    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        for pdf_file in pdf_files:
            zip_file.write(os.path.join(OUTPUT_DIR, pdf_file), pdf_file)
    return zip_filename

# Function to handle file uploads and template selection
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    # Retrieve form data
    tarif_type = request.form.get('tarifType')
    energy_type = request.form.get('energyType')
    contract_duration = request.form.get('contractDuration')
    counter_type = request.form.get('counterType')

    # Determine the correct template based on form inputs
    if tarif_type == "Spot":
        template_name = f"spot_tarif_template_{energy_type}_{counter_type}.pdf"
    elif tarif_type == "Portfolio":
        template_name = f"portfolio_tarif_template_{energy_type}_{contract_duration}.pdf"
    else:
        flash("Invalid contract type selected.")
        return redirect(request.url)
    
    pdf_template_path = os.path.join(TEMPLATE_DIR, template_name)
    
    # Check if the template exists
    if not os.path.exists(pdf_template_path):
        flash(f"Template not found: {template_name}")
        return redirect(request.url)

    # Save the uploaded file
    excel_path = os.path.join(TEMPLATE_DIR, file.filename)
    file.save(excel_path)

    # Generate PDFs from the uploaded Excel file
    create_output_directory()
    
    try:
        pdf_files = create_contracts_from_excel(excel_path, pdf_template_path)
    except FileNotFoundError as e:
        flash(str(e))
        return redirect(request.url)
    
    if not pdf_files:
        flash("No contracts were generated.")
        return redirect(request.url)
    
    zip_filename = create_zip(pdf_files)
    
    return render_template('success.html', pdf_files=pdf_files, zip_file=zip_filename)

# Route for the index page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return upload_file()  # Delegate to the upload_file function
    return render_template('index.html')

# Route for downloading individual PDFs
@app.route('/download/<filename>', methods=['GET'])
def download_pdf(filename):
    pdf_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(pdf_path):
        flash(f"File {filename} not found.")
        return redirect(url_for('index'))
    return send_file(pdf_path, as_attachment=True)

# Route for downloading the zip file of all contracts
@app.route('/download_zip', methods=['GET'])
def download_zip():
    zip_path = os.path.join(OUTPUT_DIR, "contracts.zip")
    if not os.path.exists(zip_path):
        flash("Zip file not found.")
        return redirect(url_for('index'))
    return send_file(zip_path, as_attachment=True)

# Route for downloading the Excel template
@app.route('/download_template', methods=['GET'])  # New route for the Excel template
def download_template():
    if not os.path.exists(EXCEL_TEMPLATE_PATH):
        flash("Excel template not found.")
        return redirect(url_for('index'))
    return send_file(EXCEL_TEMPLATE_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)  # Allow external connections
