"""Rebuild all stages; --clean archives earlier generated versions before rebuilding."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean',action='store_true',help='Move generated directories to work/rebuild_backups, then regenerate from source inputs.')
    args=parser.parse_args()
    if args.clean:
        destination=ROOT/'work/rebuild_backups'/str(time.time_ns())
        destination.mkdir(parents=True,exist_ok=True)
        for name in ['data','outputs']:
            target=(ROOT/name).resolve()
            assert target.parent==ROOT.resolve() and not (ROOT/name).is_symlink()
            if target.exists():
                shutil.move(str(target),str(destination/name))
    env=os.environ.copy()
    env['MPLCONFIGDIR']=str(ROOT/'work/matplotlib')
    env['PYTHONUTF8']='1'
    for path in sorted((ROOT/'src').glob('[0-9][0-9]_*.py')):
        print(f'Running {path.name}',flush=True)
        subprocess.run([sys.executable,str(path)],cwd=ROOT,env=env,check=True)
        if path.name.startswith('07_'):
            results=ROOT/'outputs/results.json'
            R=json.loads(results.read_text(encoding='utf-8'))
            R['rebuild']={'clean_generated_directories':args.clean,'all_prior_stages_ran':True,
                          'method':'Source workbook re-read; generated directories archived outside active paths before clean rebuild.'}
            results.write_text(json.dumps(R,indent=2,ensure_ascii=False),encoding='utf-8')
    subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,env=env,check=True)
    print('All stages and tests passed.',flush=True)

if __name__=='__main__':
    main()
