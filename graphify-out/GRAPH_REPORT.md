# Graph Report - D:\code\ata-v2  (2026-10-01)

## Corpus Check
- Corpus is ~29,500 words - fits in a single context window. You may not need a graph.

## Summary
- 676 nodes · 1875 edges · 71 communities (53 shown, 18 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70

## God Nodes (most connected - your core abstractions)
1. `push()` - 66 edges
2. `add()` - 59 edges
3. `replace()` - 48 edges
4. `remove()` - 39 edges
5. `has()` - 38 edges
6. `get()` - 36 edges
7. `clone()` - 29 edges
8. `some()` - 26 edges
9. `split()` - 25 edges
10. `decl()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `ATAHandler` --uses--> `ThesisAgent`  [INFERRED]
  server.py → core/roles.py
- `run_server()` --calls--> `init_db()`  [INFERRED]
  server.py → core/db.py
- `get_connection()` --references--> `_Connection`  [EXTRACTED]
  core/db.py → core/gates.py
- `ThesisAgent` --uses--> `OpenRouterClient`  [INFERRED]
  core/roles.py → core/openrouter_client.py

## Import Cycles
- None detected.

## Communities (71 total, 18 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (65): _a(), Ae(), applyParallelOffset(), ax(), Bf(), Cc(), clone(), cloneAfter() (+57 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (5): Bh(), displayType(), J2(), QS(), ruleVendorPrefixes()

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (31): An(), atrule(), block(), body(), comment(), decl(), document(), emptyRule() (+23 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (29): ca(), cr(), cs(), DC(), El(), F_(), fS(), get() (+21 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (28): br(), comma(), cx(), dx(), ec(), Fh(), fx(), gx() (+20 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (25): add(), already(), au(), cleanFromUnprefixed(), cleanOtherPrefixes(), clear(), cloneBefore(), convert() (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (24): content(), css(), dp(), Eh(), getAsyncError(), getIterator(), getProxyProcessor(), handleError() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (23): ao(), cy(), Dl(), dy(), error(), fromOffset(), fy(), G2() (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (19): addToError(), Jn(), Md(), Nt(), rawBeforeClose(), rawBeforeComment(), rawBeforeOpen(), rawBeforeRule() (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (17): action(), api(), esc(), examples, files, history, knowledgeNames, loadGates() (+9 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (9): OpenRouterClient, Any, OpenRouter Client for ATA v2 (Advanced Thesis Architect) Integrates OpenRouter…, Send a chat completion request to OpenRouter with fallback among free models., Any, roles.py - Academic Persona & Role Engine for ATA v2 Implements all prompts and…, Execute a specific thesis assistant role, read_knowledge_file() (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.20
Nodes (16): after(), append(), BC(), c2(), Co(), ei(), en(), f2() (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.37
Nodes (13): _assessment(), _Connection, evaluate_g1(), evaluate_g2(), evaluate_g3(), evaluate_g4(), evaluate_g5(), evaluate_g6() (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.24
Nodes (12): B(), c(), E(), ea(), J(), lx(), N(), _t() (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (14): before(), delete(), _deleteIfExpired(), entriesDescending(), _getItemValue(), _getOrDeleteIfExpired(), h_(), il() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (13): aa(), ac(), b2(), bx(), Cl(), nn(), Sg(), sn() (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.21
Nodes (13): checkForWarning(), contain3d(), disabled(), disabledDecl(), disabledValue(), gridStatus(), H5(), Hn() (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.27
Nodes (11): check_doi_crossref(), check_doi_openalex(), Any, verify_citations.py - Deterministik Citation Verifier for ATA v2 Verifies DOIs…, Verify single citation across Crossref and OpenAlex, Verify list of DOIs and return structured report, Check DOI via Crossref API, Check DOI via OpenAlex API (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.27
Nodes (8): get_connection(), init_db(), log_ai_usage(), db.py - SQLite Database Engine for ATA v2 Implements the 10-Tier Data Model…, Initialize database tables according to ATA v2 Specification, update_directive_status(), server.py - High-Performance Local Backend Server for ATA v2 Serves the Dual-…, run_server()

### Community 20 - "Community 20"
Cohesion: 0.22
Nodes (11): constructor(), createTokenizer(), mapResolve(), positionBy(), positionInside(), possible(), prefixeds(), rangeBy() (+3 more)

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (5): get_directives(), Any, ATAHandler, Any, SimpleHTTPRequestHandler

### Community 22 - "Community 22"
Cohesion: 0.24
Nodes (10): beforeAfter(), calcBefore(), cleanBrackets(), maxPrefixed(), process(), raw(), rawBeforeDecl(), restoreBefore() (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.33
Nodes (3): parse_draft_claims(), Conservative sentence audit. Reference presence is not evidence verification., EngineTests

### Community 24 - "Community 24"
Cohesion: 0.32
Nodes (7): normalize_text(), Any, quote_check.py - Exact and Fuzzy Quote Verifier for ATA v2 Ensures direct…, Normalize whitespace and punctuation for resilient matching, Verify if a quote exists verbatim in source_text. If not exact match, checks…, run_acceptance_test(), verify_quote()

### Community 25 - "Community 25"
Cohesion: 0.29
Nodes (8): arbitraryProperty(), create(), d2(), forVariant(), I2(), recordVariant(), recordVariants(), zg()

### Community 26 - "Community 26"
Cohesion: 0.32
Nodes (8): check(), isHack(), isNot(), isOr(), isProp(), remove(), toRemove(), withHackValue()

### Community 27 - "Community 27"
Cohesion: 0.25
Nodes (8): convertDirection(), fixAngle(), fixDirection(), fixRadial(), isRadial(), newDirection(), revertDirection(), roundFloat()

### Community 28 - "Community 28"
Cohesion: 0.32
Nodes (8): isStretch(), old(), prefixed(), prefixer(), regexp(), V0(), values(), virtual()

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (7): _2(), as(), E2(), O2(), Pl(), sort(), T2()

### Community 30 - "Community 30"
Cohesion: 0.33
Nodes (6): blueGray(), coolGray(), lightBlue(), qr(), trueGray(), warmGray()

### Community 31 - "Community 31"
Cohesion: 0.33
Nodes (6): group(), otherPrefixes(), parentPrefix(), prefixes(), unprefixed(), withPrefix()

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (6): hh(), Kn(), $p(), V1(), Xn(), z1()

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (6): Ig(), k2(), Ne(), qg(), Rl(), Y2()

### Community 34 - "Community 34"
Cohesion: 0.40
Nodes (6): negative(), qe(), sx(), tn(), xt(), Yf()

### Community 35 - "Community 35"
Cohesion: 0.33
Nodes (6): rawIndent(), reduceSpaces(), showSourceCode(), split(), toString(), Ug()

### Community 36 - "Community 36"
Cohesion: 0.70
Nodes (5): Ah(), g_(), jo(), Sh(), y_()

### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (5): _emitEvictions(), _entriesAscending(), _moveToRecent(), resize(), _set()

### Community 38 - "Community 38"
Cohesion: 0.67
Nodes (4): async(), catch(), finally(), then()

### Community 39 - "Community 39"
Cohesion: 0.50
Nodes (4): clean(), div(), prefixName(), prefixQuery()

### Community 40 - "Community 40"
Cohesion: 0.67
Nodes (4): cloneDiv(), colorStops(), oldDirection(), oldWebkit()

### Community 41 - "Community 41"
Cohesion: 0.50
Nodes (4): dm(), eE(), hm(), X()

### Community 42 - "Community 42"
Cohesion: 0.67
Nodes (3): applyVariantOffset(), compare(), Lh()

### Community 43 - "Community 43"
Cohesion: 0.67
Nodes (3): bd(), ja(), Jk()

### Community 44 - "Community 44"
Cohesion: 0.67
Nodes (3): bo(), TC(), Ue()

### Community 45 - "Community 45"
Cohesion: 0.67
Nodes (3): checkMissedSemicolon(), colon(), doubleColon()

### Community 46 - "Community 46"
Cohesion: 0.67
Nodes (3): cm(), mm(), rE()

### Community 47 - "Community 47"
Cohesion: 0.67
Nodes (3): gk(), Np(), yk()

### Community 48 - "Community 48"
Cohesion: 0.67
Nodes (3): go(), Ht(), sr()

### Community 49 - "Community 49"
Cohesion: 1.00
Nodes (3): gR(), M0(), Yu()

### Community 50 - "Community 50"
Cohesion: 0.67
Nodes (3): LS(), ro(), To()

### Community 51 - "Community 51"
Cohesion: 0.67
Nodes (3): OA(), Pa(), wk()

### Community 52 - "Community 52"
Cohesion: 0.67
Nodes (3): qh(), recalculateVariantOffsets(), remapArbitraryVariantOffsets()

## Knowledge Gaps
- **6 isolated node(s):** `{chromium}`, `roles`, `history`, `files`, `knowledgeNames` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `replace()` connect `Community 8` to `Community 0`, `Community 40`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `prefixed()` connect `Community 28` to `Community 2`, `Community 8`, `Community 16`, `Community 22`, `Community 31`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `add()` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 8`, `Community 11`, `Community 13`, `Community 16`, `Community 20`, `Community 22`, `Community 26`, `Community 28`, `Community 31`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **What connects `{chromium}`, `roles`, `history` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06386946386946386 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03508771929824561 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.0989247311827957 - nodes in this community are weakly interconnected._