"""Build a notebook containing the actual workflow code; execute and compare results."""
import json
import os
import subprocess
import sys
import nbformat
from common import ROOT, start, load_results, save_results, finish

def main():
    start()
    expected=load_results()
    nb=nbformat.v4.new_notebook()
    cells=[nbformat.v4.new_markdown_cell('# Identifying Patterns in Global E-Commerce Sales\n\nExecutable workflow using only the supplied workbook and assignment brief. Money is merchandise value in pounds; cancellation allocation is retrospective. See the report for scope and limitations.'),
           nbformat.v4.new_code_cell("# Locate the repository, import the shared definitions, and keep execution reproducible.\nfrom pathlib import Path\nimport os, sys, json\nroot = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'AGENTS.md').exists())\nos.chdir(root)\nsys.path.insert(0, str(root/'src'))")]
    titles=['Load, clean and chronologically net cancellations','Exploratory analysis','Customer features and outlier rule','Compare models, fit, profile, save and reload','Name segments and propose actions']
    scripts=['01_clean_and_net.py','02_eda.py','03_features.py','04_model.py','05_segments.py']
    for title,script in zip(titles,scripts):
        cells.append(nbformat.v4.new_markdown_cell('## '+title+'\n\nThe following cell contains the complete stage implementation. It runs the same functions used by the command-line pipeline.'))
        source=(ROOT/'src'/script).read_text(encoding='utf-8')
        cells.append(nbformat.v4.new_code_cell(source))
    cells.append(nbformat.v4.new_markdown_cell('## Inspect saved figures and their computed captions'))
    cells.append(nbformat.v4.new_code_cell("from IPython.display import display, Image, Markdown\nR = json.loads((root/'outputs/results.json').read_text(encoding='utf-8'))\nfor key, info in R['figures'].items():\n    display(Image(filename=str(root/f'outputs/figures/{key}.png'), width=1000))\n    display(Markdown(info['caption']))"))
    cells.append(nbformat.v4.new_markdown_cell('## Reload and score raw customer inputs'))
    cells.append(nbformat.v4.new_code_cell("# AOV is internally consistent, and the exact fitted feature order is preserved.\nimport joblib\nimport pandas as pd\nmodel = joblib.load(root/'outputs/model/customer_segmentation.joblib')\nfeatures = R['model']['features']\nprint('Feature order:', ', '.join(features))\nprint('Selected k:', R['model']['k'])\nexample = pd.DataFrame([R['model_test']['inputs']])[features]\nlabel = str(int(model.predict(example)[0]))\nassert label == R['model_test']['label']\nassert R['model_test']['inputs']['AOV'] == R['model_test']['inputs']['Monetary']/R['model_test']['inputs']['Frequency']\nprint(example.to_string(index=False))\nprint(R['segments'][label]['name'])\nprint(pd.DataFrame(R['segments']).T.to_string())\nprint('Recorded regression checks:', R['regression'])"))
    cells.append(nbformat.v4.new_markdown_cell('## How AI was used\n\nAI assisted with code, debugging, narrative drafting and validation. All numerical claims come from executed computations against the supplied files. Group members must review the reasoning, verify the citation, complete the ethics declaration and explain the notebook themselves. AI is an authoring tool, not a source of new retail facts.'))
    nb.cells=cells
    nb.metadata.kernelspec={'display_name':'Retail project','language':'python','name':'retail-project'}
    path=ROOT/'outputs/notebook/retail_segmentation.ipynb'
    nbformat.write(nb,path)
    kernel=ROOT/'work/jupyter/kernels/retail-project'
    kernel.mkdir(parents=True,exist_ok=True)
    (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Retail project','language':'python'}),encoding='utf-8')
    env=os.environ.copy()
    env['JUPYTER_PATH']=str(ROOT/'work/jupyter')
    env['JUPYTER_RUNTIME_DIR']=str(ROOT/'work/jupyter/runtime')
    env['IPYTHONDIR']=str(ROOT/'work/ipython')
    env['MPLCONFIGDIR']=str(ROOT/'work/matplotlib')
    subprocess.run([sys.executable,'-m','nbconvert','--to','notebook','--execute','--inplace',str(path),
                    '--ExecutePreprocessor.timeout=1800','--ExecutePreprocessor.kernel_name=retail-project'],cwd=ROOT,env=env,check=True)
    executed=nbformat.read(path,as_version=4)
    assert all(c.get('execution_count') is not None for c in executed.cells if c.cell_type=='code')
    assert not any(o.output_type=='error' for c in executed.cells if c.cell_type=='code' for o in c.outputs)
    actual=load_results()
    for key in ['regression','missing_id','products','countries','outliers','model_test','segments','model','features','seasonal','cancellations_monthly']:
        assert actual[key]==expected[key], key
    actual['notebook']={'executed':True,'code_cells':sum(c.cell_type=='code' for c in executed.cells),'comparison':'Regression, missing IDs, EDA findings, outliers, feature diagnostics, every model selection metric, model test and segment profiles identical to command-line run.'}
    save_results(actual)
    finish('Executed notebook','Notebook includes full stage source, saved outputs and embedded plots; nbconvert completed without cell errors. Core numerical results match the earlier command-line run. Notebook kernel registration is project-local.')

if __name__=='__main__':
    main()
