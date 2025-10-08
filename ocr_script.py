import os
import sys
import json
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# ===== CONFIG =====
PDF_INPUT_DIR = "orders"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure PDF pipeline
pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

def process_pdf(pdf_path: str):
    pdf_name = Path(pdf_path).stem
    pdf_output_dir = Path(OUTPUT_DIR) / pdf_name
    pdf_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔄 Processing: {pdf_name}")

    # Convert PDF → Docling document
    result = doc_converter.convert(pdf_path)
    doc = result.document

    # --- Export to multiple formats ---
    outputs = {
        "text": doc.export_to_text(),
        "markdown": doc.export_to_markdown(),
        "json": doc.export_to_dict(),
        "html": doc.export_to_html(),
        "doctags": doc.export_to_doctags(),
    }

    # Save each output
    for fmt, content in outputs.items():
        out_file = pdf_output_dir / f"{pdf_name}.{fmt if fmt != 'json' else 'json'}"
        if fmt == "json":
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        else:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)

    # --- Extract texts only (cleaned/normalized) ---
    texts_only = [t["text"] for t in outputs["json"].get("texts", []) if "text" in t]

    texts_only_file = pdf_output_dir / f"{pdf_name}_texts_only.json"
    with open(texts_only_file, "w", encoding="utf-8") as f:
        json.dump({"texts": texts_only}, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved outputs to: {pdf_output_dir}")
    print(f"📝 Extra texts-only JSON saved as: {texts_only_file}\n")


if __name__ == "__main__":
    input_dir = Path(PDF_INPUT_DIR)
    if not input_dir.exists():
        print(f"❌ Input folder '{PDF_INPUT_DIR}' not found. Please create it and add PDFs.")
        sys.exit(1)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️ No PDFs found in {PDF_INPUT_DIR}")
        sys.exit(1)

    processed_count = 0
    skipped_count = 0

    for pdf in pdf_files:
        pdf_name = pdf.stem
        output_folder = Path(OUTPUT_DIR) / pdf_name
        expected_text_output = output_folder / f"{pdf_name}.text"

        # Skip if already processed (exists and non-empty)
        if expected_text_output.exists() and expected_text_output.stat().st_size > 0:
            print(f"⏭️ Skipping '{pdf_name}' — already processed.")
            skipped_count += 1
            continue

        process_pdf(str(pdf))
        processed_count += 1

    print(f"\nSummary:")
    print(f"🆕 Processed new PDFs: {processed_count}")
    print(f"⏩ Skipped already processed: {skipped_count}")
