import os
import subprocess
import fitz  # PyMuPDF
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

def doc_to_docx(doc_path):
    """
    将 .doc 文件转换为 .docx 格式（使用 MacOS 内置的 textutil）
    """
    if not doc_path.endswith('.doc'):
        return doc_path
    
    docx_path = doc_path + 'x'
    try:
        subprocess.run(['textutil', '-convert', 'docx', doc_path], check=True)
        return docx_path
    except Exception as e:
        print(f"Error converting {doc_path} to docx: {e}")
        return None

def docx_to_md(docx_path, output_md_path):
    """
    将 .docx 文件转换为 Markdown 格式
    """
    doc = docx.Document(docx_path)
    md_content = []

    for element in doc.element.body:
        if isinstance(element, docx.oxml.text.paragraph.CT_P):
            para = Paragraph(element, doc)
            text = para.text.strip()
            if not text:
                continue
            
            # 简单的标题识别 (基于样式名称)
            style = para.style.name if para.style else ""
            if style.startswith('Heading'):
                level = style.replace('Heading', '').strip()
                if level.isdigit():
                    prefix = '#' * int(level)
                    md_content.append(f"{prefix} {text}")
                else:
                    md_content.append(f"## {text}")
            else:
                md_content.append(text)
        
        elif isinstance(element, docx.oxml.table.CT_Tbl):
            table = Table(element, doc)
            md_table = []
            for i, row in enumerate(table.rows):
                row_data = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                md_table.append("| " + " | ".join(row_data) + " |")
                if i == 0:
                    # 添加分割线
                    md_table.append("| " + " | ".join(['---'] * len(row_data)) + " |")
            md_content.append("\n".join(md_table))
            md_content.append("")

    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(md_content))

def pdf_to_md(pdf_path, output_md_path):
    """
    将 PDF 文件转换为 Markdown 格式 (基础文本提取)
    """
    doc = fitz.open(pdf_path)
    md_content = []

    for page in doc:
        # 获取页面文本
        text = page.get_text("text")
        md_content.append(text)
    
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(md_content))

def main():
    target_dir = "/Users/yangjie/code/antigravity/电气操作管理/电气操作"
    files = os.listdir(target_dir)
    
    for file in files:
        if file.startswith('.'): continue
        
        file_path = os.path.join(target_dir, file)
        base_name = os.path.splitext(file)[0]
        output_md = os.path.join(target_dir, f"{base_name}.md")
        
        print(f"Processing: {file}")
        
        if file.endswith('.pdf'):
            pdf_to_md(file_path, output_md)
            print(f"Converted PDF to MD: {output_md}")
        
        elif file.endswith('.doc'):
            docx_path = doc_to_docx(file_path)
            if docx_path:
                docx_to_md(docx_path, output_md)
                # 转换完后可以删除临时生成的 docx
                if os.path.exists(docx_path):
                    os.remove(docx_path)
                print(f"Converted DOC to MD: {output_md}")
        
        elif file.endswith('.docx'):
            docx_to_md(file_path, output_md)
            print(f"Converted DOCX to MD: {output_md}")

if __name__ == "__main__":
    main()
