import subprocess
import img2pdf
import hashlib
import os
import shutil
import PyPDF2
import io


def convert_pdf(input: bytes, type: str):
    if type == "image":
        return img2pdf.convert(input)
    if type == "docs":
        workdir = "tmp/"+hashlib.sha256(input).hexdigest()
        os.makedirs(workdir,exist_ok=True)
        with open(workdir+"/source", "wb") as f:
            f.write(input)
        subprocess.run(["soffice", "--headless", "--convert-to",
                       "pdf", "--outdir", workdir, workdir+"/source"])
        with open(workdir+"/source.pdf","rb") as f:
            file = f.read()
        shutil.rmtree(workdir)
        return file
    if type == "pdf":
        return input


def merge_pdf(to: str, src: dict):
    merger = PyPDF2.PdfMerger()
    if os.path.exists("data/{}".format(to)):
        fd = open("data/{}".format(to), "rb+")
        merger.append(fileobj=fd)
        fd.seek(0)
    else:
        fd = open("data/{}".format(to), "wb")
    for k, items in src.items():
        for i, v in enumerate(items):
            byteIO = io.BytesIO(convert_pdf(v, k))
            pdf = PyPDF2.PdfReader(byteIO)
            merger.append(pdf)
            byteIO.close()
    merger.write(fd)
    merger.close()

def remove_page(target, *page_nums):
    with open("data/"+target, 'rb+') as f:
        pdf_reader = PyPDF2.PdfFileReader(f, strict=False)
        pdf_writer = PyPDF2.PdfFileWriter()

        skip_page = 0
        all_page = pdf_reader.numPages
        for i in range(all_page):
            if i + skip_page in page_nums:
                continue
            pdf_page = pdf_reader.getPage(i)
            pdf_writer.addPage(pdf_page)

        f.seek(0)
        pdf_writer.write(f)

def export_page(target,*page_nums):
    pdf_writer = PyPDF2.PdfWriter()
    with open("data/"+target, 'rb') as f:
        pdf_reader = PyPDF2.PdfFileReader(f, strict=False)

        all_page = pdf_reader.numPages
        for i in range(all_page):
            if i in page_nums:
                print(i,page_nums)
                pdf_page = pdf_reader.getPage(i)
                pdf_writer.addPage(pdf_page)
            else:
                continue
        with io.BytesIO() as o:
            pdf_writer.write_stream(o)
            o.seek(0)
            return o.read()

if __name__ == "__main__":
    remove_page("dummy.pdf",0,2)