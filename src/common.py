"""Shared definitions, native JSON, figure checks and stage audit trail."""
from pathlib import Path
import json
import subprocess
import textwrap
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
ALL_FEATURES = ['Recency', 'Frequency', 'Monetary', 'AOV', 'Variety', 'CancellationRate']
RFM = ALL_FEATURES[:3]

def native(x):
    if isinstance(x, dict):
        return {str(k): native(v) for k,v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [native(v) for v in x]
    if isinstance(x, (np.integer, np.floating, np.bool_)):
        return native(x.item())
    if isinstance(x, (pd.Timestamp, Path)):
        return str(x)
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x

def save_results(R, path=ROOT/'outputs/results.json'):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(native(R), indent=2, ensure_ascii=False), encoding='utf-8')

def load_results():
    return json.loads((ROOT/'outputs/results.json').read_text(encoding='utf-8'))

def start():
    rules = (ROOT/'AGENTS.md').read_text(encoding='utf-8')
    assert '# NON-NEGOTIABLE RULES' in rules and 'R11.' in rules
    for p in ['data','outputs/figures','outputs/docs','outputs/model','outputs/report','outputs/demo','outputs/notebook']:
        (ROOT/p).mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':12, 'axes.spines.top':False,'axes.spines.right':False,
                         'axes.titleweight':'bold','axes.labelcolor':'#263b4c','figure.facecolor':'white'})
    return time.perf_counter()

def finish(stage, message):
    print(message, flush=True)
    with (ROOT/'PROGRESS.md').open('a',encoding='utf-8') as f:
        f.write(f'\n{stage}: {message}\n')
    # Add existing paths individually, so stages before README creation are committed too.
    for p in ['src','tests','docs','outputs','PROGRESS.md','README.md','requirements.txt','run_all.py','.gitignore','.gitattributes']:
        if (ROOT/p).exists():
            result=subprocess.run(['git','add',p],cwd=ROOT,capture_output=True,text=True)
            if result.returncode:
                raise RuntimeError('Stage completed but Git staging failed: '+result.stderr)
    subprocess.run(['git','-c','user.name=Codex','-c','user.email=codex@local','commit','-m',f'{stage}: verified generated artifacts'],cwd=ROOT,capture_output=True)

def figure(R, fig, key, caption):
    fig.tight_layout(rect=(0,.14,1,.94))
    fig.text(.025,.025,textwrap.fill(caption,int(fig.get_figwidth()*10)),fontsize=9,va='bottom')
    fig.canvas.draw()
    axes_checks=[]
    for ax in fig.axes:
        limits = [*ax.get_xlim(), *ax.get_ylim()]
        assert np.isfinite(limits).all()
        for t in ax.texts:
            xy = ax.transAxes.inverted().transform(t.get_transform().transform(t.get_position()))
            assert -.05 <= xy[0] <= 1.05 and -.05 <= xy[1] <= 1.05, (key,t.get_text(),xy)
        axes_checks.append(limits)
    path=ROOT/f'outputs/figures/{key}.png'
    fig.savefig(path,dpi=220)
    title=fig._suptitle.get_text() if fig._suptitle else fig.axes[0].get_title()
    R.setdefault('figures',{})[key]={'title':title,'caption':caption,'axis_limits':axes_checks,'dpi':220}
    plt.close(fig)

def read_net():
    return pd.read_parquet(ROOT/'data/net_purchases.parquet')

def words(text):
    """Count whitespace-delimited words, keeping formatted numbers as single words."""
    return len(text.split())
