# Redesign NacSovet Hugo Site — Caucasian Mountainous Aesthetic, Flat Design

## What to do

Analyze the existing NacSovet Hugo site structure (review `/layouts/`, `/content/news/`, `config.toml`) and create a completely new visual design with a Caucasian mountainous aesthetic while preserving:

- All Hugo templates and their logic (pagination, sidebar filters, archives, search)
- All existing content and front matter
- Mobile responsiveness and functionality
- Component structure and data flow
- Layout and structure (right sidebar, featured section, archive cards)

**Reference:** A `project-info.md` file will contain the new organization's details (company name, contact info, structure tweaks). Use this to customize the site for the new organization while keeping the identical tech stack and blogging functionality intact.

---

## Design Direction

### Concept: Caucasian Mountainous Aesthetic
Create a design inspired by the Caucasus landscape — natural, earthy, rich in heritage. Think:
- **Mountain stone textures** — solid, grounded, timeless
- **Earthy, warm tones** — clay, stone, earth colors
- **Natural, organic feel** — not corporate, but authentic and welcoming
- **Light, minimal surface** — the whole site stays light; paper color, no borders on content; typography and whitespace do the work (see "Block Rules"); mountain-ridge separators on header and footer give the Caucasus character
- **Premium feel through type and space** — strong Manrope headings, relaxed Inter body, generous section spacing
- **Square corners only** — `border-radius: 0` everywhere (no rounded corners)
- **Deep, readable typography** — strong hierarchy, WCAG AA minimum for body text

---

## Color Palette (Caucasian Earthy Tones)

### Primary Colors
- **Primary (Deep Charcoal):** `#2B2620` — **text only**, never a background fill
- **Secondary (Warm Clay):** `#C4866D` — Terracotta/clay, warm earth tone
- **Accent (Mountain Stone):** `#8B7355` — Muted brown, like weathered stone
- **Alt Accent (Warm Gold):** `#D4A574` — Warm sand/gold highlights

### Supporting Colors
- **Background (Paper):** `#F5F3F0` — Warm off-white, like aged paper
- **Text Primary:** `#2B2620` — Same as primary (excellent contrast)
- **Text Secondary:** `#5A5550` — Darker muted tone for body text
- **Sidebar Tint (Warm Stone Tint):** `#EDE8E0` — background of sidebar widgets only; text on it meets WCAG AA (Text Primary and Text Secondary both pass)
- **Hover/Active:** `#C4866D` (warm clay) — for decorative ridge lines and rules only; hover/active text on paper or the sidebar tint is shown with Primary text color and an underline (clay and stone do not reach AA contrast as body-size text)

### Accent Variations
- **Success:** `#6B8E5F` — Forest green (Caucasus forests)
- **Warning:** `#C4866D` — Warm clay (already in palette)
- **Danger:** `#8B5A4F` — Darker rust tone

---

## Typography (Keep Same Fonts)

- **Headings:** Manrope, sans-serif (same as before)
- **Body:** Inter, sans-serif (same as before)
- **Monospace:** Fira Code (same as before)

### Typography Hierarchy
- **H1 / featured title:** 4xl+, Manrope font-extrabold, line-height tight, color primary
- **H2:** 2xl, font-bold, line-height tight, color primary
- **H3:** xl, font-semibold, color primary
- **H4:** lg, font-semibold, color primary
- **Body:** Inter, base (16px), font-normal, color text-secondary, line-height relaxed (1.75)
- **Small/Meta:** sm, font-normal, color text-secondary (no opacity reduction, to keep AA contrast)

---

## Design System Changes

### Corners
- **All corners SQUARE** — `border-radius: 0` everywhere
- Buttons, cards, inputs, badges, pills, modals and images → `0` radius (remove every `rounded-*` utility from the design)

### Flat Only (no depth effects)
- **No box-shadows** — remove every `shadow-*` class
- **No gradients**
- **No blur or glass effects** — no `backdrop-blur`, no translucent "frosted" surfaces
- No outlines or hover lifts; definition comes from spacing and typography only

### Block Rules (Light Minimal Surface)
- **The whole site stays LIGHT.** No black or dark blocks anywhere, including the header and footer. Charcoal `#2B2620` is for text only, never a background fill.
- **Page, header, footer, main wrapper, content area, news section, featured item and every archive item** use the paper background `#F5F3F0`, with no borders and no tint. Separate them with spacing only.
- **Only the sidebar widgets** get their own surface: the Sidebar Tint `#EDE8E0` with **no border**, so they read as distinct from the main content.
- **No borders on content:** remove all `border`, `border-*`, `divide-*` and `ring` classes from content blocks. The only lines in the design are the mountain-ridge separators (header bottom, footer top) and the optional 1px clay rule under the header ridge.
- **Separation by spacing and typography:** padding and margin (consistent section gaps) plus size, weight, color and line-height.
- Hover/active states on content use color/weight change on text (Primary, with underline), not background or border.

### Spacing
- Generous, consistent section spacing; keep the current padding and gaps as the minimum and increase vertical gaps between sections
- Line height: relaxed for body text (1.75)
- Body text contrast: WCAG AA minimum against both `#F5F3F0` (paper) and `#EDE8E0` (sidebar tint); use Text Primary `#2B2620` or Text Secondary `#5A5550`

### Mountain Ridge Separator (shared)
- A decorative inline SVG: jagged peaks, full width, about **12 to 16px tall**, with `viewBox` and `width="100%"` (preserveAspectRatio `none`) so it scales with the screen width, including on mobile.
- Fill or stroke in Warm Clay `#C4866D` or Mountain Stone `#8B7355` (palette colors only).
- Mark it `aria-hidden="true"` (and `focusable="false"`); it is purely decorative. No rounded corners, no shadow, no gradient.
- Used twice: at the **bottom edge of the header** and, **mirrored vertically**, along the **top edge of the footer**, so header and footer match.

### Header Style
- **Light:** paper background `#F5F3F0`; text, navigation and logo in charcoal `#2B2620`. No dark band.
- **Mountain ridge separator** at the bottom edge (see above); optionally a thin **1px clay rule** (`#C4866D`) directly under the ridge.
- Logo and navigation separated by spacing and type weight, not lines or cells
- Navigation in a clean, linear layout; bold, readable typography; hover = underline
- Search input and buttons in the header: square, flat, no border (contrast comes from text color and padding)

### Sidebar Widgets
- Each widget is a flat block with the Sidebar Tint `#EDE8E0` background, **no border**, no shadow, comfortable inner padding and spacing between widgets
- Widget heading: **bold, uppercase** Manrope, small size, letter-spaced, in Text Primary, with a **short accent underline in Mountain Stone `#8B7355`** (decorative bar, e.g. 32 to 48px wide, 2px thick)
- Filter chips, inputs and counters are square and unboxed (text styles only)

### Main Content Area
- **Featured item:** largest element on the page: Manrope 4xl+ heading, generous spacing above and below; paper background, no border, no tint
- **Archive items:** horizontal rows (image left, text right) on paper, separated by vertical spacing only; title in Manrope bold, meta in small Text Secondary, hover = title color/underline change only
- **Pagination:** unboxed numbers/links in Inter, current page shown by weight and Primary color
- **Footer:** light, same paper color `#F5F3F0`, with the mirrored mountain ridge separator along its top edge; text in charcoal / Text Secondary
- Hierarchy runs from featured item (largest) down to archive titles (medium) and meta (smallest)

### Mobile
- Blocks stack full-width with the same padding as desktop
- Header and footer ridge separators scale with the width (SVG `viewBox`, `width: 100%`)
- The sidebar toggle stays unchanged (same behavior and position)
- All touch targets remain accessible

---

## Keep Identical

- All Tailwind utility classes (adapt to new color palette)
- Alpine.js interactivity (menus, toggles, filters, search)
- Hugo template logic and variable names
- All pagination, search, archive filtering functionality
- Component structure (`/components/header.html`, `/components/footer.html`, etc.)
- Partials and helpers
- Front matter structure
- **Tech stack and blogging functionality**
- **Layout structure** (right sidebar, featured section, archive)
- **Responsiveness** (mobile-first, same breakpoints)

---

## Output

1. **Design System & Colors**
   - Update `tailwind.config.js` with new Caucasian color palette
   - Define all border-radius as `0` (square corners)
   - Set new typography scale

2. **Header Redesign**
   - New header layout (light paper background, charcoal text, mountain ridge separator at the bottom)
   - Light header (paper background, charcoal text) with the mountain ridge separator at the bottom edge (+ optional 1px clay rule)
   - Logo and navigation separated by spacing
   - Navigation styled simply and readably

3. **Template Updates** (`/layouts/`)
   - `_default/home.html` — flat featured section on paper (no shadows, no borders, no block backgrounds)
   - `_default/list.html` — unboxed sidebar widgets, archive rows separated by spacing
   - `_default/single.html` — flat design for post detail page
   - Update all color references to new palette

4. **Styling Approach**
   - Remove all `shadow-*`, `border*`, `divide-*`, `ring*` and content-block `bg-*` classes (spacing and type replace them)
   - Square all corners → `0` border-radius
   - Use new color palette throughout
   - Keep spacing and readability intact
   - Maintain flat, paper-like aesthetic

5. **Organization Customization**
   - Update `config.toml` with new organization details from `project-info.md`
   - Update partials (header, footer, sidebar) with organization name and contact info
   - Adjust any structure-specific content as specified in `project-info.md`

6. **Testing**
   - Verify pagination still works
   - Test sidebar filters on mobile and desktop
   - Confirm search functionality operates correctly
   - Check responsive breakpoints
   - Verify new color palette is readable and accessible
   - Check that all corners are square (no rounding)

---

## Do NOT

- Add rounded corners (border-radius should be 0)
- Add shadows, gradients, blur or glass effects
- Add black or dark background blocks (header and footer included; charcoal is text only)
- Add borders, dividers or rings to content blocks, or give content blocks their own background (only the sidebar widgets use the `#EDE8E0` tint)
- Introduce colors or fonts outside this file's palette and Manrope/Inter
- Change Hugo template variables or logic
- Modify content files (`.md`, front matter)
- Add new dependencies or frameworks beyond Tailwind/Alpine
- Break existing functionality or structure
- Remove or rename partials/components
- Alter page layout or responsiveness

---

## File Structure Reference

```
project-root/
├── config.toml              (update organization details + colors here)
├── project-info.md          (reference file with new org details)
├── layouts/
│   ├── _default/
│   │   ├── home.html        (flat design featured section)
│   │   ├── list.html        (flat sidebar, flat archive cards)
│   │   └── single.html       (flat design post page)
│   ├── partials/
│   │   ├── header.html      (NEW header design + org name)
│   │   ├── footer.html      (update org name/contact)
│   │   ├── sidebar.html     (tinted `#EDE8E0` widgets, no borders)
│   │   └── post-media.html
│   └── shortcodes/
│       └── img.html         (no changes needed)
├── content/
│   └── news/               (do not modify)
└── assets/
    └── css/
        └── main.css        (update if custom CSS exists)
```

---

## Tailwind Configuration Notes

```javascript
// tailwind.config.js snippet
colors: {
    primary: '#2B2620',         // Deep charcoal
    secondary: '#C4866D',       // Warm clay
    accent: '#8B7355',          // Mountain stone
    'accent-alt': '#D4A574',    // Warm gold
    background: '#F5F3F0',      // Warm paper
    'sidebar-tint': '#EDE8E0',  // Sidebar widgets only
    'text-primary': '#2B2620',  // Same as primary
    'text-secondary': '#5A5550',// Darker muted
    success: '#6B8E5F',         // Forest green
    warning: '#C4866D',         // Warm clay
    danger: '#8B5A4F',          // Dark rust
},

borderRadius: {
    // ALL ZERO (square corners)
    'default': '0',
    'none': '0',
    'sm': '0',
    'md': '0',
    'lg': '0',
    'xl': '0',
    'full': '0',
},

fontFamily: {
    heading: ['Manrope', 'sans-serif'],
    body: ['Inter', 'sans-serif'],
    mono: ['Fira Code', 'monospace'],
},
```

---

## Success Criteria

- [ ] New Caucasian earthy color palette applied throughout
- [ ] New light header design (paper background, charcoal text, mountain ridge separator at the bottom)
- [ ] Footer is light with the mirrored ridge separator along its top edge; no black or dark blocks anywhere
- [ ] All corners square (zero border-radius)
- [ ] Flat design approach (no shadows, gradients or blur)
- [ ] Paper `#F5F3F0` for page, header, footer, wrapper, content, news section, featured item and archive items; only sidebar widgets use the `#EDE8E0` tint (no borders)
- [ ] No border, divide or ring classes in the templates
- [ ] Blocks are separated by spacing and typography hierarchy only
- [ ] Sidebar widgets flat and readable
- [ ] Main content area flat with good spacing
- [ ] Typography readable and clear
- [ ] New organization details integrated correctly
- [ ] All functionality (pagination, filters, search) works
- [ ] Mobile layout responsive and usable
- [ ] No console errors or broken links
- [ ] Hugo builds without errors
- [ ] Tech stack and blogging functionality unchanged

---

## How to Use This Prompt

### In Claude Code:
```
@Claude Code: Follow the instructions in REDESIGN-V2.md to redesign the NacSovet site with a Caucasian mountainous aesthetic.

1. First, read the `project-info.md` file to understand the new organization's details
2. Review the current /layouts/ structure and understand the existing Hugo logic
3. Then redesign with the new Caucasian color palette and flat design approach:
   - Deep charcoal (#2B2620), warm clay (#C4866D), mountain stone (#8B7355), warm paper (#F5F3F0)
   - ALL corners SQUARE (border-radius: 0)
   - NEW light header design (paper background, charcoal text, mountain ridge separator at the bottom; mirrored ridge on top of the footer)
   - Light minimal surface (paper #F5F3F0, sidebar widgets tinted #EDE8E0, no borders, no shadows; spacing and typography separate blocks)
   - Keep all spacing and readability
4. Create new header.html with a light background, charcoal text and the ridge separator
5. Update all templates to remove shadows, borders, dark blocks and per-block backgrounds (except the sidebar widget tint)
6. Ensure all corners are square throughout
7. Update color tokens in tailwind.config.js and config.toml
8. Keep all Hugo logic, variables, and functionality identical
9. Maintain layout structure and responsiveness
10. Test that pagination, search, and filters still work

Start with the header redesign, then home.html (featured section), then list.html (sidebar + archive).
```

### Quick One-Liner:
```
Read project-info.md for new org details. Redesign the NacSovet Hugo site with Caucasian mountainous aesthetic: deep charcoal (#2B2620), warm clay (#C4866D), mountain stone (#8B7355), warm paper background (#F5F3F0). Use a light minimal-surface design: paper #F5F3F0 everywhere (sidebar widgets tinted #EDE8E0), charcoal for text only (no black blocks), no borders on content, no shadows, gradients or blur, square corners (0 border-radius); mountain-ridge SVG separators on the header bottom and footer top (clay/stone); separate blocks with spacing and typography. Keep layout, structure, responsiveness, and all Hugo functionality unchanged.
```

---

**End of REDESIGN-V2.md**