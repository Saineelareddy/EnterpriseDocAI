import zlib
from pathlib import Path

def create_simple_pdf(output_path: Path):
    """Generate a clean, valid 4-page PDF for testing text extraction and page numbering."""
    content_page1 = (
        "BT\n"
        "/F1 18 Tf\n"
        "50 720 Td\n"
        "(Enterprise Security and Compliance Manual - Part 1) Tj\n"
        "/F1 12 Tf\n"
        "0 -30 Td\n"
        "(Section 1: Access Control and Identification) Tj\n"
        "0 -20 Td\n"
        "(All personnel must wear identification badges at all times within secure facilities.) Tj\n"
        "0 -20 Td\n"
        "(Access to database clusters requires explicit authorization from security leads.) Tj\n"
        "0 -20 Td\n"
        "(Multi-factor authentication is enforced across all engineering staging clusters.) Tj\n"
        "ET\n"
    ).encode("latin1")

    content_page2 = (
        "BT\n"
        "/F1 14 Tf\n"
        "50 720 Td\n"
        "(Enterprise Security and Compliance Manual - Part 2) Tj\n"
        "/F1 12 Tf\n"
        "0 -25 Td\n"
        "(Section 2: Incident Response Protocol) Tj\n"
        "0 -20 Td\n"
        "(Security incidents must be reported to soc@enterprisedoc.ai within 15 minutes.) Tj\n"
        "0 -20 Td\n"
        "(The incident response team initiates triage and isolation procedures immediately.) Tj\n"
        "0 -20 Td\n"
        "(Post-incident root cause analyses must be submitted within 72 hours of resolution.) Tj\n"
        "ET\n"
    ).encode("latin1")

    content_page3 = (
        "BT\n"
        "/F1 14 Tf\n"
        "50 720 Td\n"
        "(Enterprise Security and Compliance Manual - Part 3) Tj\n"
        "/F1 12 Tf\n"
        "0 -25 Td\n"
        "(Section 3: Compliance Standards and Data Retention) Tj\n"
        "0 -20 Td\n"
        "(The organization undergoes annual SOC 2 Type II and ISO 27001 third-party audits.) Tj\n"
        "0 -20 Td\n"
        "(Customer activity telemetry and audit trails must be retained for 7 calendar years.) Tj\n"
        "0 -20 Td\n"
        "(Deletion of production log streams before the retention period is strictly prohibited.) Tj\n"
        "ET\n"
    ).encode("latin1")

    content_page4 = (
        "BT\n"
        "/F1 14 Tf\n"
        "50 720 Td\n"
        "(Enterprise Security and Compliance Manual - Part 4) Tj\n"
        "/F1 12 Tf\n"
        "0 -25 Td\n"
        "(Section 4: Disaster Recovery and Business Continuity) Tj\n"
        "0 -20 Td\n"
        "(Database snapshots are replicated asynchronously across multi-region availability zones.) Tj\n"
        "0 -20 Td\n"
        "(The Recovery Time Objective RTO is strictly 60 minutes for tier-one applications.) Tj\n"
        "0 -20 Td\n"
        "(The Recovery Point Objective RPO is guaranteed under 5 minutes of transaction data.) Tj\n"
        "ET\n"
    ).encode("latin1")

    streams = [content_page1, content_page2, content_page3, content_page4]

    # Assemble PDF objects
    objs = []
    
    # 1: Catalog
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R 4 0 R 5 0 R 6 0 R] /Count 4 >>\nendobj\n")
    # 3: Page 1
    objs.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 7 0 R /Resources << /Font << /F1 11 0 R >> >> >>\nendobj\n")
    # 4: Page 2
    objs.append(b"4 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 8 0 R /Resources << /Font << /F1 11 0 R >> >> >>\nendobj\n")
    # 5: Page 3
    objs.append(b"5 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 9 0 R /Resources << /Font << /F1 11 0 R >> >> >>\nendobj\n")
    # 6: Page 4
    objs.append(b"6 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 10 0 R /Resources << /Font << /F1 11 0 R >> >> >>\nendobj\n")
    # 7: Stream 1
    objs.append(f"7 0 obj\n<< /Length {len(streams[0])} >>\nstream\n".encode("latin1") + streams[0] + b"\nendstream\nendobj\n")
    # 8: Stream 2
    objs.append(f"8 0 obj\n<< /Length {len(streams[1])} >>\nstream\n".encode("latin1") + streams[1] + b"\nendstream\nendobj\n")
    # 9: Stream 3
    objs.append(f"9 0 obj\n<< /Length {len(streams[2])} >>\nstream\n".encode("latin1") + streams[2] + b"\nendstream\nendobj\n")
    # 10: Stream 4
    objs.append(f"10 0 obj\n<< /Length {len(streams[3])} >>\nstream\n".encode("latin1") + streams[3] + b"\nendstream\nendobj\n")
    # 11: Font
    objs.append(b"11 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    # Calculate offsets
    pdf_header = b"%PDF-1.4\n"
    body = b""
    offsets = [0]
    
    current_offset = len(pdf_header)
    for obj in objs:
        offsets.append(current_offset)
        body += obj
        current_offset += len(obj)

    xref_offset = len(pdf_header) + len(body)
    
    xref = f"xref\n0 {len(objs) + 1}\n".encode("latin1")
    xref += b"0000000000 65535 f \n"
    for o in offsets[1:]:
        xref += f"{o:010d} 00000 n \n".encode("latin1")

    trailer = f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_header + body + xref + trailer)
    print(f"Created sample PDF at {output_path}")

if __name__ == "__main__":
    out = Path("sample_docs/sample_handbook.pdf")
    create_simple_pdf(out)
