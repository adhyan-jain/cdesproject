# Reference audit

2026-10-13. All 25 entries of `overleaf/references.bib` are cited in `main.tex` and all 25
citations resolve (checked by `tools/check_manuscript.py`). No duplicate keys.

Verification levels:

- **DOI**: title, authors, venue, year and pages were returned by the Crossref API for the DOI in the entry (queried 2026-10-13).
- **PAGE**: the cited page or file was opened and the bibliographic data read from it.
- **CODE**: the cited software was fetched at the stated version and built or run.
- **BOOK**: a standard textbook; bibliographic data from the publisher-level record or general knowledge, the book itself **not** re-read for this manuscript. The authors should check each against a physical or library copy.

| # | Key | Level | What was confirmed | What the manuscript uses it for | Open point |
|---|---|---|---|---|---|
| 1 | `aho2006` | BOOK | title, authors, 2nd ed., 2006 | definition of a scoped symbol table; per-scope tables | edition and publisher city not re-checked |
| 2 | `graham1979` | DOI | 10.1145/800229.806953; pp. 50-57; SIGPLAN Symposium on Compiler Construction 1979 | historical root of hashed scoped tables | content known only from an annotated bibliography; first names expanded from initials, **confirm** |
| 3 | `appel1998` | DOI (book) | 10.1017/CBO9781139174930, Cambridge University Press | the undo-stack scheme | chapter not re-read; Crossref lists a second contributor (M. Ginsburg) for the online edition, the print title page should decide |
| 4 | `crosby2003` | PAGE | USENIX page: title, authors, 12th USENIX Security Symposium, 2003 | algorithmic complexity attacks on hash tables | page numbers not shown on the page and therefore omitted |
| 5 | `aumasson2012` | DOI | 10.1007/978-3-642-34931-7_28; LNCS 7668; pp. 489-508 | Murmur multicollisions for any seed; SipHash | paper itself not read in full; the specific construction was read in the slides (next entry) |
| 6 | `llvmsht` | PAGE | LLVM doxygen page for `ScopedHashTable.h` | LLVM's scoped table | a web page; add an access date check before submission |
| 7 | `tcc` | CODE | repository cloned, commit 43c7708 patched and built | trace source; description of its symbol stacks | none |
| 8 | `rustchash` | PAGE | README fetched on 2026-10-13; lines 7-9 read: "...provides resistance against DOS attacks. These attacks aren't a concern in the compiler so we prefer to use a quicker, non-cryptographic hash algorithm." | unkeyed hash in a hosted compiler; the manuscript quotes "aren't a concern in the compiler" | none |
| 9 | `hanson1990` | DOI | 10.1002/spe.4380200104; vol. 20, no. 1, pp. 5-12 | region allocation by lifetime | none |
| 10 | `micropython` | PAGE | MicroPython documentation page on string interning | interned identifier pools | none |
| 11 | `knuth3` | BOOK | title, 2nd ed., 1998 | deletion in open addressing; expected probe count | section 6.4 not re-read; our measurement reproduces the formula used |
| 12 | `bender2021` | DOI | 10.1109/FOCS52979.2021.00115; pp. 1171-1182 | effect of deletions on linear probing | abstract level only |
| 13 | `celis1985` | DOI | 10.1109/SFCS.1985.48; pp. 281-288 | Robin Hood hashing | none |
| 14 | `naor2001` | DOI | 10.1145/380752.380844; pp. 492-501 | history independence | abstract level only |
| 15 | `blelloch2007` | DOI | 10.1109/FOCS.2007.36; pp. 272-282 | history-independent hashing | abstract level only |
| 16 | `pagh2007` | DOI | 10.1145/1250790.1250839; pp. 318-327 | interval-counting analysis of linear probing | abstract level only |
| 17 | `thorup2015` | PAGE | arXiv:1509.04549 listing | the same technique, lecture notes | not read in full; a preprint, acceptable as background only |
| 18 | `aumassonslides` | PAGE | PDF opened; title page lists the three authors; slide 37 states "A multicollision works for any seed" | the MurmurHash3 construction | presentation slides, not peer reviewed; the venue is not stated in the entry |
| 19 | `linuxsiphash` | PAGE | kernel documentation page | HalfSipHash-1-3 for hash tables | none |
| 20 | `metis` | CODE | repository audited at commit 7b3dacf | predecessor and baseline | authors of the entry are two of this manuscript's authors; confirm they agree to the comparison |
| 21 | `murmur3` | PAGE | SMHasher repository | the default mixer | none |
| 22 | `siphashref` | CODE | `halfsiphash.c` downloaded (SHA-256 096b33b6...8301c), compiled, compared on 200 000 inputs | conformance of the keyed hash | none |
| 23 | `chibicc` | CODE | repository cloned, commit 90d1f7f patched and built (earlier session) | second trace source | none |
| 24 | `phmap` | CODE | v1.4.1 at commit 22a7f6c fetched and compiled | Swiss-table baselines | none |
| 25 | `strata` | CODE | this project's public repository | artifact | the entry lists the four authors in the manuscript's order; add a commit or release tag once the submission version is frozen |

## Not cited, although considered

| Source | Why it is not cited |
|---|---|
| DEC RADIX-50 (precedent for packing characters below 8 bits) | only a Wikipedia page was available; the manuscript makes no claim that needs it |
| CVE-2012-0839, CVE-2012-0876 | seen only in search-result summaries |
| US patent 8,505,000 B2 (compilation without a symbol table) | only the abstract was read |
| Clang `IdentifierTable` | not needed after the related-work section was narrowed |
| Abseil Swiss tables design notes | the baseline cites the library actually used (`phmap`) |

## Retractions

None of the cited papers was found to be retracted in the Crossref records returned on
2026-10-13 (Crossref marks retractions in the `update-to` field; none was present). This was
not checked against Retraction Watch.

## What the authors should still do

1. Open each BOOK-level source and confirm the cited statement.
2. Replace or supplement web pages with archival sources where a venue requires it.
3. Read entries 12 and 14-17 beyond the abstract, since the related-work section characterises them.
