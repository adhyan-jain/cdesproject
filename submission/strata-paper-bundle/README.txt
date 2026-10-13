STRATA paper bundle

paper/main.pdf    full paper, IEEE conference format
paper/short.pdf   four-page-limit version for work-in-progress and student-research tracks
paper/            LaTeX sources of both; build with
                    pdflatex main && bibtex main && pdflatex main && pdflatex main
                  (and the same for short). The numbers in generated_numbers.tex and tables/
                  are generated from the measurements in the repository; see docs/REPRODUCE.md.
docs/             reproduction guide, contribution summary, draft cover letter, venue
                  assessment, sign-off checklist, novelty gate, readiness report

NOT READY TO SUBMIT until docs/SIGNOFF_CHECKLIST.md is complete. The sources contain visible
[AUTHOR: ...] markers for information only the authors can supply.

Repository with code, traces and raw data: https://github.com/shubhisingh1510/cdesproject
