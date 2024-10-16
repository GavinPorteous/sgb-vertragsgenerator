import os
import pandas as pd
from pdfrw import PdfReader, PdfWriter, PdfDict

# Verzeichnis- und Dateipfade
TEMPLATE_DIR = "templates/"
OUTPUT_DIR = "output/"
PDF_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "contract_template.pdf")
EXCEL_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "data_template.xlsx")

# Hilfsfunktion zum Erstellen des Output-Verzeichnisses
def create_output_directory():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# Verbesserte Funktion zum Auslesen der PDF-Felder mit Fehlerbehandlung
def get_pdf_fields(pdf_path):
    # Überprüfe, ob die PDF-Datei existiert
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Template PDF not found at {pdf_path}")

    try:
        # Versuch, die PDF-Datei zu lesen
        template_pdf = PdfReader(pdf_path)
    except Exception as e:
        raise pdfrw.errors.PdfParseError(f"Could not read PDF file {pdf_path}: {str(e)}")

    fields = {}
    for page in template_pdf.pages:
        annotations = page.Annots
        if annotations:
            for annotation in annotations:
                field_name = annotation.T
                if field_name:
                    fields[field_name[1:-1]] = None  # Entfernt Klammern um den Namen
    return fields

# Funktion zum Erstellen der PDFs
def create_contracts_from_excel(excel_path, pdf_template_path):
    # Excel-Daten laden
    df = pd.read_excel(excel_path)
    
    # Ausgabe der Spaltenüberschriften zur Fehlersuche
    print("Spalten in der Excel-Datei:", df.columns)
    
    # Felder im PDF-Template auslesen
    pdf_fields = get_pdf_fields(pdf_template_path)
    print("Felder im PDF-Template:", pdf_fields)  # Zum Überprüfen, welche Felder im PDF vorhanden sind
    
    # Anzahl leerer Zeilen verfolgen
    empty_row_count = 0
    max_empty_rows = 5

    # Durch die Excel-Zeilen iterieren
    for index, row in df.iterrows():
        if row.isnull().all():
            empty_row_count += 1
            if empty_row_count >= max_empty_rows:
                print("Zu viele leere Zeilen, Programm wird beendet.")
                break
            continue
        empty_row_count = 0

        # PDF-Daten füllen
        filled_fields = {}
        for pdf_field in pdf_fields:
            if pdf_field in row:
                filled_fields[pdf_field] = str(row[pdf_field])

        # Generieren des PDFs
        company_name = row["###company###"]  # Verwende den tatsächlichen Spaltennamen
        generate_pdf(filled_fields, pdf_template_path, company_name)

# Funktion zum Generieren des PDFs und Ausfüllen der Formularfelder
def generate_pdf(field_data, template_path, company_name):
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page in reader.pages:
        annotations = page.Annots  # Direkt auf Annots zugreifen
        if annotations:
            for annotation in annotations:
                field_name = annotation.T
                if field_name:
                    field_name_str = field_name[1:-1]  # Entferne Klammern
                    if field_name_str in field_data:
                        # Setze den Wert des Formularfeldes ohne Klammern
                        annotation.update(
                            PdfDict(V='{}'.format(field_data[field_name_str]))  # Keine Klammern
                        )

        writer.addpage(page)

    # Setze den Namen des Output-PDFs zusammen
    output_pdf_name = f"{company_name} Antrag SGB Portfolio.pdf"
    output_pdf_path = os.path.join(OUTPUT_DIR, output_pdf_name)

    # Schreibe die Seiten in die Ausgabedatei
    with open(output_pdf_path, "wb") as output_pdf_file:
        writer.write(output_pdf_file)
    
    print(f"PDF für {company_name} erstellt: {output_pdf_path}")

if __name__ == "__main__":
    # Erstelle das Output-Verzeichnis
    create_output_directory()

    # Starte den Prozess zur PDF-Erstellung
    create_contracts_from_excel(EXCEL_TEMPLATE_PATH, PDF_TEMPLATE_PATH)
