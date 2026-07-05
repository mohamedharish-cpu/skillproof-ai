import fitz
pdf=fitz.open("resume.pdf")
page=pdf[0]
text=page.get_text()
print("TEXT LENGTH =",len(text))
print(text)