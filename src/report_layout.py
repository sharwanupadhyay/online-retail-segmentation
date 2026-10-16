"""ReportLab layout and Poppler rendering, independent of analytical narrative."""
from pathlib import Path
import shutil
import subprocess
from html import escape
from PIL import Image as PILImage, ImageOps, ImageDraw
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from pypdf import PdfReader
from common import ROOT

STYLES=getSampleStyleSheet()
STYLES.add(ParagraphStyle(name='BodyRetail',fontName='Helvetica',fontSize=10.3,leading=15,spaceAfter=9,textColor=colors.HexColor('#263746'),alignment=TA_LEFT))
STYLES.add(ParagraphStyle(name='CaptionRetail',fontName='Helvetica',fontSize=8.7,leading=12,spaceAfter=8,textColor=colors.HexColor('#3d5362')))
STYLES.add(ParagraphStyle(name='CellRetail',fontName='Helvetica',fontSize=8,leading=10))
STYLES['Title'].textColor=colors.HexColor('#153e58')
STYLES['Heading1'].textColor=colors.HexColor('#153e58')
STYLES['Heading2'].textColor=colors.HexColor('#236b8e')

def para(text,style='BodyRetail'):
    return Paragraph(escape(str(text)).replace('\n','<br/>'),STYLES[style])

def table(headers,rows,widths):
    data=[[para(h,'CellRetail') for h in headers]]+[[para(v,'CellRetail') for v in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deebf2')),
         ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#7595a8')),
         ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7f9')]),
         ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
         ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#b9cbd5'))
    canvas.line(45,39,A4[0]-45,39)
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(colors.HexColor('#526977'))
    canvas.drawString(45,26,'Global e-commerce sales | Customer segmentation')
    canvas.drawRightString(A4[0]-45,26,str(doc.page))
    canvas.restoreState()

def image_page(story,key,info):
    path=ROOT/f'outputs/figures/{key}.png'
    with PILImage.open(path) as im:
        w,h=im.size
    ratio=min(505/w,620/h)
    story.extend([PageBreak(),para(info.get('title',key.replace('_',' ').capitalize()),'Heading1'),
                  Image(str(path),width=w*ratio,height=h*ratio),Spacer(1,8),para(info['caption'],'CaptionRetail')])

def build_pdf(story,path):
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=47,bottomMargin=53,title='Identifying Patterns in Global E-Commerce Sales',author='Group members: to be completed')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(path)
    for page in reader.pages:
        assert page.extract_text().strip()
    return len(reader.pages)

def render_pdf(path):
    binary=shutil.which('pdftoppm')
    if not binary:
        candidate=Path(r'C:\Users\realk\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
        if candidate.exists():
            binary=str(candidate)
    if not binary:
        raise RuntimeError('Poppler pdftoppm missing; install it and add it to PATH for visual validation.')
    dest=ROOT/'outputs/report/rendered'
    dest.mkdir(parents=True,exist_ok=True)
    subprocess.run([binary,'-r','100','-png',str(path),str(dest/'page')],check=True,capture_output=True)
    images=sorted(dest.glob('page-*.png'))
    for offset in range(0,len(images),9):
        chosen=images[offset:offset+9]
        sheet=PILImage.new('RGB',(840,1215),'#dce5ea')
        draw=ImageDraw.Draw(sheet)
        for i,p in enumerate(chosen):
            with PILImage.open(p) as im:
                thumb=ImageOps.contain(im,(265,375))
                x=(i%3)*280+8
                y=(i//3)*405+20
                sheet.paste(thumb,(x,y))
                draw.text((x,y-15),p.stem,fill='black')
        sheet.save(dest/f'contact_{offset//9}.png')
    return len(images)
