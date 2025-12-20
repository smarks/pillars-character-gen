#!/usr/bin/env python3
"""
Split a PDF into two halves.
Usage: python split_pdf.py input.pdf
Output: input_part1.pdf and input_part2.pdf
"""

import sys
from pypdf import PdfReader, PdfWriter
from pathlib import Path

def split_pdf(input_path):
    input_path = Path(input_path)
    
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return
    
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    midpoint = total_pages // 2
    
    print(f"Total pages: {total_pages}")
    print(f"Splitting at page {midpoint}")
    
    # First half
    writer1 = PdfWriter()
    for i in range(midpoint):
        writer1.add_page(reader.pages[i])
    
    output1 = input_path.stem + "_part1.pdf"
    with open(output1, "wb") as f:
        writer1.write(f)
    print(f"Created: {output1} ({midpoint} pages)")
    
    # Second half
    writer2 = PdfWriter()
    for i in range(midpoint, total_pages):
        writer2.add_page(reader.pages[i])
    
    output2 = input_path.stem + "_part2.pdf"
    with open(output2, "wb") as f:
        writer2.write(f)
    print(f"Created: {output2} ({total_pages - midpoint} pages)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_pdf.py input.pdf")
    else:
        split_pdf(sys.argv[1])