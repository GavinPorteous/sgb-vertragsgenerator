import os
import pandas as pd
from pdfrw import PdfReader, PdfWriter, PdfDict

# Directory and file paths
TEMPLATE_DIR = "document_templates/"  # New directory for different templates
OUTPUT_DIR = "output/"

# Helper function to create output directory
def create_output_directory():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# Function to dynamically choose the correct template based on inputs
def get_template_path(tarif_type, energy_type, duration=None, meter_type=None):
    if tarif_type == "portfolio":
        return os.path.join(TEMPLATE_DIR, f"portfolio_tarif_template_{energy_type}_{duration}.pdf")
    elif tarif_type == "spot":
        return os.path.join(TEMPLATE_DIR, f"spot_tarif_template_{energy_type}_{meter_type}.pdf")
    return None

# Function to create contracts from Excel and user inputs
def create_contracts_from_excel(excel_path, tarif_type, energy_type, duration=None, meter_type=None):
    create_output_directory()
    df = pd.read_excel(excel_path)
    pdf_files = []

    for index, row in df.iterrows():
        if row.isnull().all():
            continue  # Skip empty rows

        filled_fields = {f"###{col}###": str(val) for col, val in row.items()}
        company_name = row["###company###"]
        output_pdf_name = f"{company_name}_{tarif_type}_contract.pdf"
        output_pdf_path = os.path.join(OUTPUT_DIR, output_pdf_name)

        # Select correct template based on user input
        template_path = get_template_path(tarif_type, energy_type, duration, meter_type)

        # Load and modify the PDF template
        template_pdf = PdfReader(template_path)
        for page in template_pdf.pages:
            annotations = page['/Annots']
            if annotations:
                for annot in annotations:
                    if annot['/Subtype'] == '/Widget' and annot['/T']:
                        key = annot['/T'][1:-1]  # Strip out parentheses around field names
                        if key in filled_fields:
                            annot.update(PdfDict(V=filled_fields[key]))

        PdfWriter(output_pdf_path, template_pdf).write()
        pdf_files.append(output_pdf_path)

    return pdf_files

if __name__ == "__main__":
    create_output_directory()
    # Ensure you replace the function call below with the appropriate parameters as needed
    create_contracts_from_excel(EXCEL_TEMPLATE_PATH, "portfolio", "gas", duration="12", meter_type="slp")
