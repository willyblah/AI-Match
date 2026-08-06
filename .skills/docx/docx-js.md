# DOCX Library Tutorial

Generate .docx files with JavaScript/TypeScript.

**Important: Read this entire document before starting.** Critical formatting rules and common pitfalls are covered throughout - skipping sections may result in corrupted files or rendering issues.

## Setup
Assumes docx is already installed globally
If not installed: `npm install -g docx`

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Media, 
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink, 
        InternalHyperlink, TableOfContents, HeadingLevel, BorderStyle, WidthType, TabStopType, 
        TabStopPosition, UnderlineType, ShadingType, VerticalAlign, SymbolRun, PageNumber,
        FootnoteReferenceRun, Footnote, PageBreak } = require('docx');

// Create & Save
const doc = new Document({ sections: [{ children: [/* content */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer)); // Node.js
Packer.toBlob(doc).then(blob => { /* download logic */ }); // Browser
```

## Text & Formatting
```javascript
// IMPORTANT: Never use \n for line breaks - always use separate Paragraph elements
// ❌ WRONG: new TextRun("Line 1\nLine 2")
// ✅ CORRECT: new Paragraph({ children: [new TextRun("Line 1")] }), new Paragraph({ children: [new TextRun("Line 2")] })

// Basic text with all formatting options
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 200, after: 200 },
  indent: { left: 720, right: 720 },
  children: [
    new TextRun({ text: "Bold", bold: true }),
    new TextRun({ text: "Italic", italics: true }),
    new TextRun({ text: "Underlined", underline: { type: UnderlineType.DOUBLE, color: "FF0000" } }),
    new TextRun({ text: "Colored", color: "FF0000", size: 28, font: "Arial" }), // Arial default
    new TextRun({ text: "Highlighted", highlight: "yellow" }),
    new TextRun({ text: "Strikethrough", strike: true }),
    new TextRun({ text: "x2", superScript: true }),
    new TextRun({ text: "H2O", subScript: true }),
    new TextRun({ text: "SMALL CAPS", smallCaps: true }),
    new SymbolRun({ char: "2022", font: "Symbol" }), // Bullet •
    new SymbolRun({ char: "00A9", font: "Arial" })   // Copyright © - Arial for symbols
  ]
})
```

## Standard Document Formatting Specifications

When creating professional reports or formal documents, apply the following specifications. Use these as the default style system unless the user requests otherwise.

### Typography
| Element | Font | Size | Size (half-pts) |
|---------|------|------|-----------------|
| H1 | Microsoft YaHei | 26pt | 52 |
| H2 | Microsoft YaHei | 20pt | 40 |
| H3 | Microsoft YaHei | 16pt | 32 |
| H4 | Microsoft YaHei | 14pt | 28 |
| Body | Microsoft YaHei | 11pt | 22 |

### Spacing
| Element | Line spacing | Before | After |
|---------|-------------|--------|-------|
| H1 | 1.4× (`line: 336, lineRule: "auto"`) | — | — |
| H2 | 1.4× (`line: 336, lineRule: "auto"`) | 18pt (360 twips) | 8pt (160 twips) |
| H3 | — | 12pt (240 twips) | 4pt (80 twips) |
| Body | At-least 20pt (`line: 400, lineRule: "atLeast"`) | — | — |

> ⚠️ **CRITICAL — never use `lineRule: "exact"` (固定行距)**
> `"exact"` hard-clips any content taller than the specified height. This causes:
> - **文字折叠**: CJK characters (e.g. Microsoft YaHei) render slightly taller than Latin text and get clipped at the bottom
> - **图片覆盖**: images in a paragraph with `exact` spacing are clipped to the line height, making the next paragraph appear to cover the image
>
> Always use `"atLeast"` for fixed-looking spacing — it behaves identically when content fits, but expands instead of clipping when it doesn't.

### Complete Style Block (copy-paste ready)

```javascript
const { LineRuleType } = require('docx'); // add to imports if needed
const FONT = "Microsoft YaHei";

const styles = {
  default: {
    document: { run: { font: FONT, size: 22 } }  // 11pt body default
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: FONT, size: 52, bold: true, color: "000000" },
      paragraph: {
        spacing: { line: 336, lineRule: "auto" },
        outlineLevel: 0
      }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: FONT, size: 40, bold: true, color: "000000" },
      paragraph: {
        spacing: { before: 360, after: 160, line: 336, lineRule: "auto" },
        outlineLevel: 1
      }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: FONT, size: 32, bold: true, color: "000000" },
      paragraph: {
        spacing: { before: 240, after: 80, lineRule: "auto" },  // explicit "auto" — never inherit "exact"
        outlineLevel: 2
      }
    },
    {
      id: "Heading4", name: "Heading 4", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: FONT, size: 28, bold: true, color: "000000" },
      paragraph: {
        spacing: { lineRule: "auto" },  // explicit "auto" — never inherit "exact"
        outlineLevel: 3
      }
    },
    {
      id: "Normal", name: "Normal",
      run: { font: FONT, size: 22, color: "000000" },
      paragraph: {
        // "atLeast" not "exact" — exact clips CJK chars and images
        spacing: { line: 400, lineRule: "atLeast" }
      }
    },
    {
      id: "FigureCaption", name: "Figure Caption", basedOn: "Normal",
      run: { font: FONT, size: 28, color: "000000" },  // 14pt
      paragraph: {
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 }
      }
    }
  ]
};
```

### Table Standard

Light gray header (`F2F2F2`), thin borders (`D0D0D0`), header cells bold:

```javascript
const thinBorder = { style: BorderStyle.SINGLE, size: 4, color: "D0D0D0" };
const cellBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const headerShading = { fill: "F2F2F2", type: ShadingType.CLEAR };

new TableRow({
  tableHeader: true,
  children: [
    new TableCell({
      borders: cellBorders,
      shading: headerShading,
      children: [new Paragraph({
        children: [new TextRun({ text: "列标题", bold: true, font: FONT, size: 22 })]
      })]
    }),
    // more header cells...
  ]
}),
// Data rows: same cellBorders, no shading
```

### Image + Caption Standard

⚠️ **Image paragraphs MUST use `lineRule: "auto"` (or omit `spacing` entirely).** If the paragraph inherits `lineRule: "atLeast"` or `"exact"` at a small value, the image will be clipped and the following content will appear to cover it.

Max usable image width: **451pt** (A4 with 1" margins) or **468pt** (Letter with 1" margins). Never exceed these or the image overflows into the margin.

```javascript
// Image paragraph — explicit "auto" spacing, 16pt gap above image
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 320, after: 0, lineRule: "auto" },  // MUST be "auto", not "atLeast"/"exact"
  children: [new ImageRun({
    type: "png",
    data: fs.readFileSync("image.png"),
    transformation: { width: 400, height: 300 },  // width must be ≤ 451 (A4) or 468 (Letter)
    altText: { title: "图片", description: "图片描述", name: "image" }
  })]
}),
// Caption paragraph — 16pt gap below
new Paragraph({
  style: "FigureCaption",
  spacing: { before: 0, after: 320, lineRule: "auto" },
  children: [new TextRun({ text: "图1 图片标题", font: FONT, size: 28 })]
}),
```

### Header & Footer Standard

Header shows report name (left-aligned); footer shows centered page number:

```javascript
headers: {
  default: new Header({
    children: [new Paragraph({
      alignment: AlignmentType.LEFT,
      children: [new TextRun({ text: reportTitle, font: FONT, size: 18, color: "666666" })]
    })]
  })
},
footers: {
  default: new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "666666" })
      ]
    })]
  })
},
```

### Cover Page Standard

Cover is a dedicated first section (no header/footer). Push content to vertical center by setting a large `margin.top` on the section — **never use a spacer `Paragraph` with `spacing.before`** to simulate vertical offset: spacer paragraphs are easy to accidentally copy into other sections and produce large blank areas at the top of every page.

```javascript
// Section 1: cover page — large top margin centers content vertically
{
  properties: {
    page: {
      // top margin ~35% of A4 page height (≈ 4200 twips) pushes content to visual center
      margin: { top: 4200, right: 1440, bottom: 1440, left: 1440 }
    }
  },
  children: [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 480, lineRule: "auto" },
      children: [new TextRun({ text: reportTitle, font: FONT, size: 72, bold: true })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 960, lineRule: "auto" },
      children: [new TextRun({ text: subtitle, font: FONT, size: 40, color: "444444" })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { lineRule: "auto" },
      children: [new TextRun({ text: dateStr, font: FONT, size: 28, color: "888888" })]
    }),
  ]
},
// Section 2: main content — restore normal margins, add header/footer
{
  properties: {
    page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
  },
  headers: { /* ... */ },
  footers: { /* ... */ },
  children: [ /* document body */ ]
}
```

---

## Styles & Professional Formatting

```javascript
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } }, // 12pt default
    paragraphStyles: [
      // Document title style - override built-in Title style
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 56, bold: true, color: "000000", font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER } },
      // IMPORTANT: Override built-in heading styles by using their exact IDs
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: "000000", font: "Arial" }, // 16pt
        paragraph: { spacing: { before: 240, after: 240, lineRule: "auto" }, outlineLevel: 0 } }, // Required for TOC; "auto" prevents clipping
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "000000", font: "Arial" }, // 14pt
        paragraph: { spacing: { before: 180, after: 180, lineRule: "auto" }, outlineLevel: 1 } },
      // Custom styles use your own IDs
      { id: "myStyle", name: "My Style", basedOn: "Normal",
        run: { size: 28, bold: true, color: "000000" },
        paragraph: { spacing: { after: 120 }, alignment: AlignmentType.CENTER } }
    ],
    characterStyles: [{ id: "myCharStyle", name: "My Char Style",
      run: { color: "FF0000", bold: true, underline: { type: UnderlineType.SINGLE } } }]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Document Title")] }), // Uses overridden Title style
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Heading 1")] }), // Uses overridden Heading1 style
      new Paragraph({ style: "myStyle", children: [new TextRun("Custom paragraph style")] }),
      new Paragraph({ children: [
        new TextRun("Normal with "),
        new TextRun({ text: "custom char style", style: "myCharStyle" })
      ]})
    ]
  }]
});
```

**Professional Font Combinations:**
- **Arial (Headers) + Arial (Body)** - Most universally supported, clean and professional
- **Times New Roman (Headers) + Arial (Body)** - Classic serif headers with modern sans-serif body
- **Georgia (Headers) + Verdana (Body)** - Optimized for screen reading, elegant contrast

**Key Styling Principles:**
- **Override built-in styles**: Use exact IDs like "Heading1", "Heading2", "Heading3" to override Word's built-in heading styles
- **HeadingLevel constants**: `HeadingLevel.HEADING_1` uses "Heading1" style, `HeadingLevel.HEADING_2` uses "Heading2" style, etc.
- **Include outlineLevel**: Set `outlineLevel: 0` for H1, `outlineLevel: 1` for H2, etc. to ensure TOC works correctly
- **Use custom styles** instead of inline formatting for consistency
- **Set a default font** using `styles.default.document.run.font` - Arial is universally supported
- **Establish visual hierarchy** with different font sizes (titles > headers > body)
- **Add proper spacing** with `before` and `after` paragraph spacing
- **Use colors sparingly**: Default to black (000000) and shades of gray for titles and headings (heading 1, heading 2, etc.)
- **Set consistent margins** (1440 = 1 inch is standard)


## Lists (ALWAYS USE PROPER LISTS - NEVER USE UNICODE BULLETS)
```javascript
// Bullets - ALWAYS use the numbering config, NOT unicode symbols
// CRITICAL: Use LevelFormat.BULLET constant, NOT the string "bullet"
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "first-numbered-list",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "second-numbered-list", // Different reference = restarts at 1
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    children: [
      // Bullet list items
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun("First bullet point")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun("Second bullet point")] }),
      // Numbered list items
      new Paragraph({ numbering: { reference: "first-numbered-list", level: 0 },
        children: [new TextRun("First numbered item")] }),
      new Paragraph({ numbering: { reference: "first-numbered-list", level: 0 },
        children: [new TextRun("Second numbered item")] }),
      // ⚠️ CRITICAL: Different reference = INDEPENDENT list that restarts at 1
      // Same reference = CONTINUES previous numbering
      new Paragraph({ numbering: { reference: "second-numbered-list", level: 0 },
        children: [new TextRun("Starts at 1 again (because different reference)")] })
    ]
  }]
});

// ⚠️ CRITICAL NUMBERING RULE: Each reference creates an INDEPENDENT numbered list
// - Same reference = continues numbering (1, 2, 3... then 4, 5, 6...)
// - Different reference = restarts at 1 (1, 2, 3... then 1, 2, 3...)
// Use unique reference names for each separate numbered section!

// ⚠️ CRITICAL: NEVER use unicode bullets - they create fake lists that don't work properly
// new TextRun("• Item")           // WRONG
// new SymbolRun({ char: "2022" }) // WRONG
// ✅ ALWAYS use numbering config with LevelFormat.BULLET for real Word lists
```

## Tables
```javascript
// Complete table with margins, borders, headers, and bullet points
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

new Table({
  columnWidths: [4680, 4680], // ⚠️ CRITICAL: Set column widths at table level - values in DXA (twentieths of a point)
  margins: { top: 100, bottom: 100, left: 180, right: 180 }, // Set once for all cells
  rows: [
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          // ⚠️ CRITICAL: Always use ShadingType.CLEAR to prevent black backgrounds in Word.
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR }, 
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ 
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Header", bold: true, size: 22 })]
          })]
        }),
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
          children: [new Paragraph({ 
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Bullet Points", bold: true, size: 22 })]
          })]
        })
      ]
    }),
    new TableRow({
      children: [
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          children: [new Paragraph({ children: [new TextRun("Regular data")] })]
        }),
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          children: [
            new Paragraph({ 
              numbering: { reference: "bullet-list", level: 0 },
              children: [new TextRun("First bullet point")] 
            }),
            new Paragraph({ 
              numbering: { reference: "bullet-list", level: 0 },
              children: [new TextRun("Second bullet point")] 
            })
          ]
        })
      ]
    })
  ]
})
```

**IMPORTANT: Table Width & Borders**
- Use BOTH `columnWidths: [width1, width2, ...]` array AND `width: { size: X, type: WidthType.DXA }` on each cell
- Values in DXA (twentieths of a point): 1440 = 1 inch, Letter usable width = 9360 DXA (with 1" margins)
- Apply borders to individual `TableCell` elements, NOT the `Table` itself

**Precomputed Column Widths (Letter size with 1" margins = 9360 DXA total):**
- **2 columns:** `columnWidths: [4680, 4680]` (equal width)
- **3 columns:** `columnWidths: [3120, 3120, 3120]` (equal width)

## Links & Navigation
```javascript
// TOC (requires headings)
// CRITICAL: Headings MUST use `heading: HeadingLevel.HEADING_X` — NOT `style: "Heading1"` — for TOC to populate.
// ❌ WRONG (TOC will be empty): new Paragraph({ style: "Heading1", children: [new TextRun("Title")] })
// ❌ WRONG (TOC will be empty): new Paragraph({ heading: HeadingLevel.HEADING_1, style: "customHeader", children: [new TextRun("Title")] })
// ✅ CORRECT: new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Title")] })
new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),

// External link
new Paragraph({
  children: [new ExternalHyperlink({
    children: [new TextRun({ text: "Google", style: "Hyperlink" })],
    link: "https://www.google.com"
  })]
}),

// Internal link & bookmark
new Paragraph({
  children: [new InternalHyperlink({
    children: [new TextRun({ text: "Go to Section", style: "Hyperlink" })],
    anchor: "section1"
  })]
}),
new Paragraph({
  children: [new TextRun("Section Content")],
  bookmark: { id: "section1", name: "section1" }
}),
```

## Images & Media
```javascript
// Basic image with sizing & positioning
// CRITICAL: Always specify 'type' parameter - it's REQUIRED for ImageRun
new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new ImageRun({
    type: "png", // NEW REQUIREMENT: Must specify image type (png, jpg, jpeg, gif, bmp, svg)
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150, rotation: 0 }, // rotation in degrees
    altText: { title: "Logo", description: "Company logo", name: "Name" } // IMPORTANT: All three fields are required
  })]
})
```

## Page Breaks
```javascript
// Manual page break
new Paragraph({ children: [new PageBreak()] }),

// Page break before paragraph
new Paragraph({
  pageBreakBefore: true,
  children: [new TextRun("This starts on a new page")]
})

// ⚠️ CRITICAL: NEVER use PageBreak standalone - it will create invalid XML that Word cannot open
// ❌ WRONG: new PageBreak() 
// ✅ CORRECT: new Paragraph({ children: [new PageBreak()] })
```

## Headers/Footers & Page Setup
```javascript
const doc = new Document({
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }, // 1440 = 1 inch
        size: { orientation: PageOrientation.LANDSCAPE },
        pageNumbers: { start: 1, formatType: "decimal" } // "upperRoman", "lowerRoman", "upperLetter", "lowerLetter"
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({ 
        alignment: AlignmentType.RIGHT,
        children: [new TextRun("Header Text")]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ 
        alignment: AlignmentType.CENTER,
        children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] }), new TextRun(" of "), new TextRun({ children: [PageNumber.TOTAL_PAGES] })]
      })] })
    },
    children: [/* content */]
  }]
});
```

## Tabs
```javascript
new Paragraph({
  tabStops: [
    { type: TabStopType.LEFT, position: TabStopPosition.MAX / 4 },
    { type: TabStopType.CENTER, position: TabStopPosition.MAX / 2 },
    { type: TabStopType.RIGHT, position: TabStopPosition.MAX * 3 / 4 }
  ],
  children: [new TextRun("Left\tCenter\tRight")]
})
```

## Constants & Quick Reference
- **Underlines:** `SINGLE`, `DOUBLE`, `WAVY`, `DASH`
- **Borders:** `SINGLE`, `DOUBLE`, `DASHED`, `DOTTED`  
- **Numbering:** `DECIMAL` (1,2,3), `UPPER_ROMAN` (I,II,III), `LOWER_LETTER` (a,b,c)
- **Tabs:** `LEFT`, `CENTER`, `RIGHT`, `DECIMAL`
- **Symbols:** `"2022"` (•), `"00A9"` (©), `"00AE"` (®), `"2122"` (™), `"00B0"` (°), `"F070"` (✓), `"F0FC"` (✗)

## Critical Issues & Common Mistakes
- **CRITICAL: PageBreak must ALWAYS be inside a Paragraph** - standalone PageBreak creates invalid XML that Word cannot open
- **ALWAYS use ShadingType.CLEAR for table cell shading** - Never use ShadingType.SOLID (causes black background).
- Measurements in DXA (1440 = 1 inch) | Each table cell needs ≥1 Paragraph | TOC requires HeadingLevel styles only
- **ALWAYS use custom styles** with Arial font for professional appearance and proper visual hierarchy
- **ALWAYS set a default font** using `styles.default.document.run.font` - Arial recommended
- **ALWAYS use columnWidths array for tables** + individual cell widths for compatibility
- **NEVER use unicode symbols for bullets** - always use proper numbering configuration with `LevelFormat.BULLET` constant (NOT the string "bullet")
- **NEVER use \n for line breaks anywhere** - always use separate Paragraph elements for each line
- **ALWAYS use TextRun objects within Paragraph children** - never use text property directly on Paragraph
- **CRITICAL for images**: ImageRun REQUIRES `type` parameter - always specify "png", "jpg", "jpeg", "gif", "bmp", or "svg"
- **CRITICAL for bullets**: Must use `LevelFormat.BULLET` constant, not string "bullet", and include `text: "•"` for the bullet character
- **CRITICAL for numbering**: Each numbering reference creates an INDEPENDENT list. Same reference = continues numbering (1,2,3 then 4,5,6). Different reference = restarts at 1 (1,2,3 then 1,2,3). Use unique reference names for each separate numbered section!
- **CRITICAL for TOC**: Headings MUST use `heading: HeadingLevel.HEADING_X` property — using `style: "Heading1"` instead produces an empty TOC. Never combine `heading:` with a custom `style:` on the same Paragraph.
- **Tables**: Set `columnWidths` array + individual cell widths, apply borders to cells not table
- **Set table margins at TABLE level** for consistent cell padding (avoids repetition per cell)
- **CRITICAL — NEVER use a spacer Paragraph to push content down**: empty paragraphs or paragraphs with large `spacing.before` used as vertical spacers are fragile — they get copied into other sections and produce large blank areas at the top of every page. Use `margin.top` on the section `properties.page` instead.
- **CRITICAL — NEVER use `lineRule: "exact"`**: it hard-clips content taller than the value. CJK fonts (e.g. Microsoft YaHei) get bottom-clipped (文字折叠), and images in the paragraph are cropped causing the next paragraph to appear to cover them (图片覆盖). Always use `"atLeast"` for body text and `"auto"` for heading and image paragraphs.
- **CRITICAL — All heading styles MUST set `lineRule: "auto"`**: headings inherit the Normal style's `"atLeast"` spacing and will clip tall CJK characters (文字折叠) without it. Always include `spacing: { lineRule: "auto" }` in every Heading paragraph style definition.
- **CRITICAL — Image paragraph spacing must be `lineRule: "auto"`**: any inherited `"atLeast"` or `"exact"` spacing will clip the image and cause the following paragraph to visually overlap it (图片遮盖). Always set `spacing: { lineRule: "auto" }` explicitly on every paragraph that contains an `ImageRun`.
- **CRITICAL — Image width must not exceed page usable width**: A4 with 1" margins = 451pt max; Letter with 1" margins = 468pt max. Wider images overflow into the margin and shift subsequent content.