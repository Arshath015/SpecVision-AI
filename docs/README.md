# docs/

`SpecVision_AI_Summary.pdf` -- a short project summary covering what was
built and three real, reproducible test-case results (not mockups):
a text-only successful match, a real photo demonstrating a documented
computer-vision limitation (also analyzed in `../EVALUATION.md` as
"Failure #1"), and a real photo where matching/pricing succeed while CV
independently and honestly flags its own uncertainty.

To regenerate the PDF:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r ..\docs\requirements.txt
python ..\docs\generate_summary_pdf.py
```

`_build/` holds the raw source data behind every figure quoted in the
PDF -- the actual `AnalyzeResponse` JSON for both featured cases (run in
offline/demo mode, so no API cost and fully reproducible), plus the
original and CV-annotated images for the second case. Regenerating the
JSON data (if the pipeline changes) is done by re-running the pipeline
directly -- see the top of `generate_summary_pdf.py` for the exact code
used to produce it.
