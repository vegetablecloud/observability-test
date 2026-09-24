# Conpanion Design System

Conpanion AB is a Swedish Data & Analytics consultancy. The name is a contraction of *consultant*
and *companion*: the firm advises with expertise and walks the journey alongside the client. The
tagline is **"We unlock the power of data"**, and the logo symbol is a key formed from the 1 and 0
of the binary system — the answers are already in the data; the job is to unlock them.

The work is data platforms, integration, modelling, BI and governance, delivered on the
Microsoft/Azure stack alongside Databricks, Snowflake, dbt and the common BI tools.

This system is the organisation-wide visual foundation. The **brand guidelines are the authority**
for colour, typography and logo. The PowerPoint master is the authority for slide geometry, and
slide decks are one application of the foundation, not the whole of it — the same tokens,
components and rules are meant to carry prototypes, wireframes, animation and web work.

## Facts and placeholders

The sample slides and the deck template carry **placeholder content**, not approved company
facts. Confirm every figure, name and client before anything goes out.

- Conpanion has **18 consultants** (September 2026) and is growing. The stated goal is **30
  employees by 2028**. Headcount changes month to month — never hard-code it into a reusable
  template.
- The contact block, presenter name, team photos and client logos are all placeholders.
- **Conpanion is not tied to Helsingborg.** The two supplied photographs show a Swedish harbour
  city; treat them as generic imagery and do not caption them with a place name.

## Sources given

| Source | What was taken from it |
| --- | --- |
| `uploads/Conpanion Brand Guidelines V1.0 - WIP.pdf` (v1.0, 2023, 26 pp.) | Brand story, strategy, values, voice, four design principles, logo family and construction, clear space, the primary colour palette, and the full typographic system (weights, leading, tracking, scale, block spacing) |
| `uploads/Conpanion Powerpoint layout.pptx` | Slide master, 11 slide layouts, the 1280×720 grid, the icon set and technology logo sheet, two cover photographs |
| `uploads/Conpanion företagspresentation.pptx`, `uploads/Workshop - våra kompetensområden.pptx` | Two decks Conpanion has actually delivered. Read for recurring slide patterns (agenda, key figures, timeline, team, client wall, closing question) and for real figures. Working files, not brand law — where they differ from the guidelines, the guidelines win |
| `uploads/Conpanion logo.svg`, `Key.svg`, `WordmarkTag.svg` | Vector logo lockup, key mark, wordmark + tagline |
| `uploads/LinkedIn Banner*.png`, `LinkedIn Profile*.png` | Social banner and profile grounds |

No Figma file, website or codebase was provided. The raw unpacked PowerPoint is kept in
`pptx_raw/` for reference.

### Where the guidelines overruled the PowerPoint

The deck template was built first, from the .pptx alone. The guidelines corrected it:

- Black is **#000000**, not the #333333 the PowerPoint theme used.
- The light ground is **Grey 50 #FAFAFA**, not the warm #FAF8F2 / #F1F0EB pair.
- `#FBAE40` (orange) and `#939B98` (grey-green) are **not brand colours** and have been removed.
- Type is **Inter** and **Roboto Mono**, not Segoe UI and Calibri. Headings are SemiBold 600, not Bold 700.
- Headings now carry the guideline tracking (−25) and leading multipliers.

## Content fundamentals

The guidelines define voice explicitly; the copy in `slides/` and the deck template is our
placeholder text and should be replaced.

- **Three words: Tydlig. Trygg. Framåtlutad.** (Clear. Confident. Forward-leaning.) Conpanion
  speaks as a partner who understands both people and data — confident without arrogance,
  expert-driven without being over-technical.
- **Short sentences. Clear messages. No buzzwords without substance.** Say what is delivered, not
  what is "leveraged". "One governed model", not "a holistic single source of truth".
- **A conpanion is** knowledgeable, clear, curious, modern, dependable, solution-oriented, human,
  forward-leaning. **A conpanion is not** arrogant, over-technical, impersonal, bureaucratic,
  reactive or corporate.
- **Person.** "We" for Conpanion, "you"/"your" for the client. We act, the client benefits.
- **Language.** Swedish-first company, English-capable material. The tagline and messaging lines
  are English; internal and client-facing decks are often Swedish. Write one deck in one language.
- **Casing.** Sentence case in headings and body — "We unlock the power of data". The wordmark is
  lowercase. Uppercase is reserved for detail copy set in Roboto Mono (eyebrows, captions, CTAs).
- **Punctuation.** No exclamation marks. Bullets are fragments without trailing full stops; body
  sentences take full stops.
- **Emoji.** Never. The icon set covers every pictogram need.
- **Numbers.** Swedish conventions in Swedish material (2026-09-21 dates, space thousands separator).

**Messaging lines from the guidelines** (use verbatim, don't paraphrase): We unlock the power of
data. From complexity to clarity. Data with direction. Turn insight into action. Built for better
decisions. Beyond dashboards. Into impact. Clarity changes everything. From gut feeling to
informed decisions. The potential is already in your data. We help you unlock it.

**The enemy** the brand argues against: complexity without clarity, data without direction, silos,
old ways of working, decisions on gut feeling, settling for reports instead of real change.

**Design principles** (the filter for any creative decision): *Banbrytande* — challenge old ways
of working. *Framåtlutade* — driven by curiosity and momentum. *Mänskliga* — technology is about
people. *Trygga* — deep expertise, calm delivery, no needless complexity.

## Visual foundations

**Colour.** Four colours, and only four: **Imperial Yellow #FFB400**, **Black #000000**,
**Grey 300 #D6D6D6**, **Grey 50 #FAFAFA**. The strategy is deliberately narrow — black, white and
grey, with Imperial Yellow given room to create energy, contrast and recognition. Yellow should be
present through the whole brand experience but used with intention: large yellow fields are
allowed and can be striking (section dividers, end cards, campaign surfaces), but inside a
document or interface yellow marks the one thing that matters. A small set of pure-K greys
(#4D4D4D, #707070, #EDEDED) is derived for secondary text and sunken surfaces; never introduce a
hue. Three legal grounds: Grey 50, Yellow, Black. Black text on yellow — never white.

**Type.** **Inter** in exactly two weights — Regular 400 for body copy and subheads, SemiBold 600
for headings. No other weight is on brand. **Roboto Mono Regular** is the detail voice: captions,
figure labels, eyebrows, metadata and calls to action. Both load from Google Fonts, so these are
the real faces.

- Leading by level: extra-large headers ×0.8, headers ×0.9, subheads ×1.0 (set solid), body ×1.2,
  captions ×1.2. Bigger type, tighter leading.
- Tracking: headlines −25 (−0.025em), subheads −10, body 0, detail/mono +50 (0.05em).
- Scale: contrast between levels must be obvious — think 1X / 3X / 10X, never 18pt body under a
  24pt heading.
- Space between text blocks is measured in cap heights: one cap height between blocks, half a cap
  height for a tight pair (`--block-gap`, `--block-gap-tight`).

**Logo.** Lockup (symbol + wordmark) is the default. The wordmark alone is used only when the
symbol is already nearby; the symbol alone where brand recognition is already high — products,
email signatures, internal material. Clear space on all sides is **X = the height of the "0" in
the symbol**. Inside the lockup, spacing is set by the width of the letter "i", and the symbol
aligns to the wordmark's cap height and baseline. The wordmark is Visby CF Black (Connary Fagen);
that licence is not included here, so **never re-typeset the wordmark** — always place the
supplied asset.

**Spacing and layout.** The slide grid is rigid: 88px side margins, title block at y=38
(1104×62), body from y=155, two-column content 544px + 16px gutter, icon grids 374px columns with
~28px gutters. Everything on a slide is absolutely positioned on the 1280×720 stage. Screen and
document work uses the same 4/8-based scale plus the cap-height rhythm.

**Backgrounds.** Flat colour, full-bleed photography, or photography under a black veil at ~45%
so type stays legible. No gradients anywhere. No textures, no patterns, no illustration. The two
supplied photographs are cool-daylight aerials of a Swedish harbour city — the photographic
register is documentary and unfiltered, not warm or grainy.

**Corners, borders, shadows.** Square. No rounded corners, no shadows, no elevation system. Cards
are flat: white surface, 1px Grey 300 hairline, optional 3px yellow rule at the top. An icon card
on a slide has no container at all — icon, heading and body stacked in a column.

**Transparency and blur.** One use only: the black veil over cover photography. No frosted glass,
no blurs, no soft protection gradients. The yellow panel on the cover slide is the protection
device — an opaque rectangle the type sits inside.

**Motion, hover, press.** Neither source defines motion, so these are house rules for screen work:
120–240ms, `ease-out`, opacity and colour only. Hover on yellow → #FFC333; press → #E6A200. No
scale on press, no bounces, no springs, no parallax. Links are black with a yellow underline that
thickens on hover.

**The fixed slide furniture.** Every content slide carries a 38px yellow bar along the bottom edge
and the key mark at x=1178, y=38, 48×101px. Section dividers and full-bleed slides drop the bar.
The mark is yellow on light and on dark, black on yellow.

## Iconography

The PowerPoint template ships **63 brand icons and 17 technology logos as PNGs** — all copied into
`assets/icons/` and `assets/tech/`. Nothing here was drawn or substituted.

- Brand icons are one consistent line set: outline only, uniform ~2px stroke, rounded caps and
  joins, drawn entirely in `#FFB400` on transparent ground, roughly 66px tall on a slide. Subjects
  are business and data metaphors: charts, databases, pipelines, teams, targets, compasses,
  clipboards, buildings. Use them at 60–66px; never recolour them, never mix them with another
  icon library, never fall back to emoji or unicode glyphs.
- Technology logos are the vendors' own full-colour marks — Azure, Azure DevOps, Azure Data Lake,
  Azure Synapse, Databricks, Snowflake, Qlik, Power BI, Tableau, Looker, Google BigQuery,
  Microsoft Fabric, SQL Server, dbt, Dynamics 365, Apache Spark, Python. These are the only place
  colour outside the brand palette is allowed. Keep them at equal optical height; never recolour.
- There is no icon font and no SVG icon set. If you need a glyph the set does not cover, ask for
  it rather than drawing one.
- Emoji are never used.

## Open points

- The guidelines are marked **WIP v1.0**. There is no guidance yet for photography art direction,
  illustration, data-visualisation colour, or digital UI patterns — the interaction rules above
  are ours, not the brand team's.
- The favicon is described in the guidelines as an optically adjusted, specially drawn version of
  the symbol. That artwork was not supplied as a file, so `assets/key-mark.svg` stands in.
- The guideline text names the body face inconsistently ("Instrument Sans" in one sentence, Inter
  throughout the specimens and weight lists). We followed the specimens: **Inter**.

## Index

- `styles.css` — the single entry point; imports everything below
- `tokens/` — `fonts.css`, `colors.css`, `typography.css`, `spacing.css`, `motion.css`, `slide.css`
- `assets/` — logos (`logo-lockup.svg`, `key-mark.svg`, `wordmark-tagline.svg`, raster variants),
  `icons/` (63 brand icons), `tech/` (17 partner logos), two photographs, four LinkedIn banners
- `guidelines/` — foundation specimen cards for Colors, Type, Spacing and Brand
- `components/core/`, `components/brand/`, `components/slides/` — the reusable primitives
- `slides/` — 11 sample slides, one per layout in the source template
- `templates/conpanion-deck/` — the ready-to-copy Conpanion deck template
- `templates/demo-deck/` — demo & explainer deck with animated diagrams (see below)
- `pptx_raw/` — unpacked source PowerPoint, kept for reference
- `SKILL.md` — agent-skill wrapper

### Components

Core: **Button**, **Tag**, **Eyebrow**, **Card**.
Brand: **KeyMark**, **KeyPhoto**, **Logo**.
Slides: **SlideFrame**, **SlideTitle**, **BulletList**, **IconCard**, **ContactBlock**, **TechLogo**.

Sample slides (compositions, in `slides/`): TitleSlide, AgendaSlide, SectionSlide,
TitleContentSlide, TwoContentSlide, ThreeIconSlide, SixIconSlide, KeyNumbersSlide, TimelineSlide,
TeamSlide, ImageLeftSlide, TechLogoSlide, ClientsSlide, StatementSlide, FullBleedSlide,
QuestionsSlide, KeyPhotoSlide, EndCardSlide.

**Deck order.** The template runs cover → agenda → section divider → content → close. The last
slide is always the key mark filled with a photograph on black; that closing frame is the one
fixed convention. Nothing else is compulsory — take the layouts a deck needs and delete the rest.

### Demo & explainer deck — step builds

`templates/demo-deck/` is for demos, workshops and knowledge sharing: architecture diagram, flow
sequence, before/after and a live-demo handoff slide. Animation comes from `cp-steps.js`, driven by
attributes, so any slide can use it:

- `<section data-steps>` makes the slide step-build; add `data-loop` to cycle the highlight once
  every step is shown.
- `data-step="n"` reveals an element at step n; `data-only="n"` shows it only at step n (captions).
- `data-active="n"` gives a yellow border at step n (use on nodes with a `#D6D6D6` 2px border).
- `data-flow` on an SVG line or path adds marching dashes; `data-progress` is a bar that fills
  across the steps; `data-pulse` is an always-on pulse (live marker).
- → / Space advance a step before the slide changes; ← steps back. Print and PDF show every step.

Diagram rules: nodes are white, square, 2px `#D6D6D6` border, with a brand icon, a mono index and
a semibold name. Groups use a 1px dashed `#A3A3A3` border with a mono uppercase label. Connectors are
2px black with a solid arrowhead. Yellow marks only what is active now.

### Intentional additions

- **Button, Tag, Eyebrow, Card** — neither source defines UI components, so this is a minimal
  standard set, built strictly from guideline values (square corners, mono uppercase detail copy,
  hairline borders, no shadow). Extend it rather than inventing a parallel style.
- **StatementSlide**, **TechLogoSlide**, **AgendaSlide**, **KeyNumbersSlide**, **TimelineSlide**,
  **TeamSlide**, **ClientsSlide** and **QuestionsSlide** are not literal layouts in the .pptx.
  The template's blank layouts (8, 10, 11) are empty containers; these give them a brand-correct
  use, rebuilt from patterns that recur in Conpanion's own decks (`Conpanion företagspresentation`
  and `Workshop - våra kompetensområden`): a numbered agenda, a key-figures row, a company
  timeline, a team grid, a client logo wall and a closing question slide.
- Derived greys, yellow hover/press values and the motion tokens are ours, flagged as such in the
  token files.

### Source layout → sample slide

| .pptx layout | Sample slide |
| --- | --- |
| 1 — photo cover with yellow contact panel | `slides/title-slide.html` |
| 2 — title only | covered by `SlideFrame` + `SlideTitle` |
| 3 — title + content | `slides/title-content-slide.html` |
| 4 — two content | `slides/two-content-slide.html` |
| 5 — three picture + text cards | `slides/three-icon-slide.html` |
| 6 — six picture + text cards | `slides/six-icon-slide.html` |
| 7 — half-bleed image left | `slides/image-left-slide.html` |
| 8 — blank | `slides/statement-slide.html` (addition) |
| 9 — yellow section divider | `slides/section-slide.html` |
| 10 — full-bleed yellow end card | `slides/end-card-slide.html` |
| 11 — full-bleed photograph | `slides/full-bleed-slide.html`, `slides/key-photo-slide.html` |
