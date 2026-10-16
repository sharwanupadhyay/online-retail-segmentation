"""Write submission documentation and script, then validate cross-artifact contracts."""
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from common import ROOT, start, load_results, save_results, finish, words
from deliverable_text import video_script, source_documentation, readme, assumptions_documentation
from validation import verify

def main():
    start()
    R=load_results()
    if os.name=='nt':
        R['runtime_notes']=[
            'Windows notebook execution emitted a Proactor/ZeroMQ warning: Tornado registered a selector thread because add_reader is unavailable on that event loop. The fallback completed successfully; no notebook cell has an error output.',
            'The local notebook kernel emitted a plain-TCP transport warning. This concerns notebook transport, not a statistical validation result; the notebook is not being deployed as a remote service.']
        with (ROOT/'PROGRESS.md').open('a',encoding='utf-8') as f:
            f.write('\nExplained notebook runtime messages: '+' '.join(R['runtime_notes'])+'\n')
    script=video_script(R)
    (ROOT/'outputs/demo/Video_Script.md').write_text(script,encoding='utf-8')
    (ROOT/'outputs/docs/Dataset_Source_Documentation.md').write_text(source_documentation(R),encoding='utf-8')
    (ROOT/'outputs/docs/Assumptions_and_Limitations.md').write_text(assumptions_documentation(R),encoding='utf-8')
    (ROOT/'README.md').write_text(readme(R),encoding='utf-8')
    R['demo']={'script_words':words(script),'recorded':False,'format':'Only spoken text; single presenter, first-person plural, separate paragraphs.'}
    # Visual review is asserted only when the human-visible inspection record matches the current PDF.
    review=ROOT/'docs/visual_review.json'
    if review.exists():
        record=json.loads(review.read_text(encoding='utf-8'))
        digest=hashlib.sha256((ROOT/'outputs/report/Project_Report.pdf').read_bytes()).hexdigest()
        if record.get('pdf_sha256')==digest and record.get('all_pages_viewed'):
            R['report']['visual_inspection']='Rendered pages inspected in this session; current PDF digest matches review record.'
            R['report']['visual_review_verified']=True
    save_results(R)
    checks=verify(R,require_clean=True)
    tested=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True)
    print(tested.stdout,flush=True)
    if tested.returncode:
        raise RuntimeError(tested.stdout+tested.stderr)
    matched=re.search(r'(\d+) passed',tested.stdout)
    checks['tests_passed']=int(matched.group(1))
    checks['visual_review_verified']=R['report'].get('visual_review_verified',False)
    R['verification']=checks
    save_results(R)
    (ROOT/'outputs/docs/verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    templates=json.loads((ROOT/'docs/requirements_template.json').read_text())
    human={1:'Group size and actual identities must be confirmed by the group.',2:'Signed declaration was not supplied.',6:'Actual collaboration and mutual review must be performed by the group.',19:'Local repository is committed; no GitHub remote was created.',21:'Spoken script and model test supplied; actual recording or live delivery must be performed by the group.'}
    lines=['# Requirements checklist','', '## Supplied assignment brief','']
    for i,item in enumerate(templates):
        text=item.format(**R['assignment'])
        lines.append(f"- [{' ' if i in human else 'x'}] {text}"+(f' **Human action:** {human[i]}' if i in human else ''))
    lines+=['','## Requested technical stages','']
    for item in ['Original-list regression checks pass before extra code exclusions.',
                 'Strictly earlier customer/product cancellation netting; partial and unmatched quantities audited.',
                 'Monthly, product, export-country and cancellation findings with computed captions.',
                 'Customer features, correlations, skew and recomputed log-Monetary outlier fence.',
                 'Complete feature-set/k metrics, seed stability, deterministic pipeline and reload test.',
                 'Segment names validated against tags; quantified sizes/revenue and distinct actions.',
                 'Notebook executed with outputs and matching core results.',
                 'Report has required structure, full cleaning audit, profiles, figures, limitations and provisional references.',
                 'Spoken-only script has required paragraph order and verified word count.',
                 'Dataset documentation, pinned requirements, README, tests and rebuild entry point.',
                 'Full rebuild began without active generated directories; earlier versions archived; all scripts compile and tests pass.',
                 'Numeric, feature-order and segment-name/action agreement checks pass.']:
        lines.append('- [x] '+item)
    lines.append(f"- [{'x' if checks['visual_review_verified'] else ' '}] Latest PDF pages visually inspected; "+('review record matches this PDF.' if checks['visual_review_verified'] else 'rendered previews exist; visual review remains pending.'))
    lines+=['','## Scope and submission constraints','',
            f"Brief due date: {R['assignment']['due_date']}; local access: {R['source']['access_date']}. Deadline arrangements, group authorship and ethics completion require human confirmation. The supplied brief references a declaration section that is absent from the supplied file. The source citation/DOI remains explicitly provisional because external factual sources were excluded by request.",
            'No video file has been generated, approved or uploaded. The deliverable is the requested spoken script and executable demonstration.']
    (ROOT/'docs/requirements_checklist.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'outputs/docs/requirements_checklist.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    verification_text=f"""# Verification

Clean rebuild: {checks['clean_rebuild']}. Executed notebook: {checks['notebook_executed']}. Syntax complete: {checks['syntax_complete']}. Feature agreement: {checks['feature_agreement']}. Segment names and actions agree: {checks['segment_names_and_actions_agree']}. Cancellation-unit conservation: {checks['cancellation_conservation']}.

Tests passed: {checks['tests_passed']}. Report word count: {checks['report_words']}, including prose, headings, table cells and accessible figure captions, excluding cover, references and repeated page furniture. Spoken script words: {checks['script_words']}. Report pages rendered: {R['report']['rendered_pages']}. Visual review matches current report: {checks['visual_review_verified']}.

Numeric tokens in the report, script, README and dataset documentation were compared with results.json using explicit numeric formatting and the permitted figure/section/candidate-k allowances. Results, profile tables, names and pipeline inputs use stable keys. The notebook recomputed the analysis and its core results were compared to the command-line run.

Human tasks remain: signed ethics declaration, real group participation and identities, course/submission placeholders, source citation verification, actual demo recording/live delivery and GitHub publication. These are not marked complete.
"""
    (ROOT/'outputs/docs/Verification.md').write_text(verification_text,encoding='utf-8')
    # Check newly written readiness and verification text as well.
    verify(R,require_clean=True)
    finish('Documentation and verification','Cross-artifact numerical, feature, segment, notebook, syntax and word-count checks passed; independent pytest suite passed. Clean generated-directory rebuild confirmed. Latest PDF visual review status is recorded in verification.json. Signed ethics declaration, actual group review, identity placeholders, citation/DOI verification, recording/live delivery and GitHub publication remain human actions.')
    archive=ROOT/'outputs/retail_assignment_repository.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file():
                continue
            rel=p.relative_to(ROOT)
            if rel.parts[0] in ['.git','.venv','work','data'] or '__pycache__' in rel.parts or '.pytest_cache' in rel.parts:
                continue
            if p.suffix in ['.zip','.xlsx'] or 'rendered' in rel.parts:
                continue
            z.write(p,str(rel))
    print('Repository archive created:',archive.name,flush=True)

if __name__=='__main__':
    main()
