"""Cross-artifact verification using native results as the numeric source of truth."""
import ast
import json
import re
import py_compile
import importlib
import numpy as np
import pandas as pd
import nbformat
from pypdf import PdfReader
from PIL import Image
from common import ROOT, ALL_FEATURES, words

NUMBER=re.compile(r'(?<![\w])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)*(?:%)?')

def numeric_tokens(text):
    # Numeric substrings inside filenames, URLs and software versions are still checked.
    return set(NUMBER.findall(text))

def allowed_numbers(R):
    allowed=set()
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                allowed.update(numeric_tokens(str(k)))
                walk(v)
        elif isinstance(x,list):
            for v in x:
                walk(v)
        elif isinstance(x,(int,float)) and not isinstance(x,bool):
            if np.isfinite(x):
                for digits in range(5):
                    allowed.update(numeric_tokens(f'{x:,.{digits}f}'))
                    allowed.update(numeric_tokens(f'{x:.{digits}f}'))
                    allowed.update(numeric_tokens(f'{x:.{digits}%}'))
                    allowed.update(numeric_tokens(f'{100*x:.{digits}f}'))
                allowed.update(numeric_tokens(str(x)))
                allowed.update(numeric_tokens(str(x)+'%'))
        elif isinstance(x,str):
            allowed.update(numeric_tokens(x))
    walk(R)
    # User's explicit allowances: figure/section numbering and candidate k values.
    allowed.update(str(v) for v in range(1,11))
    return allowed

def verify(R,require_clean=True):
    report_pdf=ROOT/'outputs/report/Project_Report.pdf'
    pdftext='\n'.join(p.extract_text() for p in PdfReader(report_pdf).pages)
    script=(ROOT/'outputs/demo/Video_Script.md').read_text(encoding='utf-8')
    report=(ROOT/'outputs/report/report_body.txt').read_text(encoding='utf-8')
    docs=[ROOT/'README.md',ROOT/'docs/requirements_checklist.md',ROOT/'PROGRESS.md',*list((ROOT/'outputs/docs').glob('*.md'))]
    texts={'report':pdftext,'script':script,**{str(p.relative_to(ROOT)):p.read_text(encoding='utf-8') for p in docs}}
    allowed=allowed_numbers(R)
    unexpected={k:sorted(numeric_tokens(v)-allowed) for k,v in texts.items() if numeric_tokens(v)-allowed}
    assert not unexpected, unexpected
    assert 2300<=words(report)<=2700,words(report)
    assert 650<=words(script)<=720,words(script)
    assert len(script.strip().split('\n\n'))==7
    assert not re.search(r'(?im)^\s*(#|\||[-*]\s|\d+[.)]\s)',script)
    assert not re.search(r'(?i)on.screen|timestamp|word count|pre.recording|speaker\s*\d|visuals?\s*:',script)
    assert script.lstrip().startswith('We ')
    canonical=', '.join(R['model']['features'])
    notebook=nbformat.read(ROOT/'outputs/notebook/retail_segmentation.ipynb',as_version=4)
    nb_all='\n'.join(c.source+'\n'+'\n'.join(o.get('text','') for o in c.get('outputs',[])) for c in notebook.cells)
    for name,content in [('report',report),('video',script),('notebook',nb_all),('README',texts['README.md'])]:
        assert canonical in content,(name,canonical)
    k=R['model']['k']
    assert f'with {k} clusters' in report
    assert f'selected {k} clusters' in script
    assert f'Selected k: {k}' in nb_all
    assert R['features']['all']==ALL_FEATURES
    assert json.loads((ROOT/'outputs/model/feature_columns.json').read_text())==R['model']['features']
    names=json.loads((ROOT/'outputs/model/segment_names.json').read_text())
    validate_name=importlib.import_module('05_segments').validate_name
    for key,s in R['segments'].items():
        assert names[key]['name']==s['name'] and names[key]['action']==s['action']
        validate_name(s['name'],s['tags'])
        assert s['name'] in script and s['name'] in report
        assert s['action'] in script and s['action'] in report
    assert len(R['figures'])>=5
    figure_checks={}
    for key,info in R['figures'].items():
        with Image.open(ROOT/f'outputs/figures/{key}.png') as im:
            assert im.width>0 and im.height>0
        assert info['caption']
        assert info['dpi']>=200
        figure_checks[key]=True
    assert all(c.execution_count is not None for c in notebook.cells if c.cell_type=='code')
    assert not any(o.output_type=='error' for c in notebook.cells if c.cell_type=='code' for o in c.outputs)
    for path in [*list((ROOT/'src').glob('*.py')),*list((ROOT/'tests').glob('*.py')),ROOT/'run_all.py']:
        source=path.read_text(encoding='utf-8')
        ast.parse(source)
        py_compile.compile(str(path),doraise=True)
        assert source.endswith('\n'),path
    f=pd.read_parquet(ROOT/'data/customer_segments.parquet')
    assert np.isclose(f.Monetary.sum(),R['netting']['net_revenue'])
    assert R['netting']['matched']+R['netting']['partly_matched']+R['netting']['unmatched']==R['netting']['cancellation_rows']
    assert np.isclose(R['netting']['reversed_units']+R['netting']['unmatched_units'],R['netting']['cancelled_units'])
    if require_clean:
        assert R['rebuild']['clean_generated_directories'] and R['rebuild']['all_prior_stages_ran']
    return dict(numeric_tokens_checked={k:len(numeric_tokens(v)) for k,v in texts.items()},
                report_words=words(report),script_words=words(script),figures=figure_checks,
                notebook_executed=True,syntax_complete=True,feature_agreement=True,segment_names_and_actions_agree=True,
                cancellation_conservation=True,clean_rebuild=R.get('rebuild',{}).get('clean_generated_directories',False))
