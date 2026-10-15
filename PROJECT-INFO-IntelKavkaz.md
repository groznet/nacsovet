# Project Info: IntelKavkaz

## Organization Details

**Organization Name:** Региональное отделение Всероссийской ассоциации общественных объединений «Интеллектуальная Россия» в Чеченской Республике (Regional Division of the All-Russian Association of Public Organizations "Intellectual Russia" in the Chechen Republic)

**Short Name:** IntelKavkaz / Интеллектуальный Кавказ

**Leadership:** Мовлатов Лом-Али Ибрагимович (Chairman)

**Organization Type:** Non-Profit / Public Association

**Main Focus:** Intellectual community development, public initiatives, educational and enlightenment projects, news and material publications

---

## Site Details

**Domain:** intelkavkaz.ru

**Site Type:** News Portal / Organization Website

**Primary Language:** Russian

**Main Purpose:** Publish news, articles, event announcements, project information, and organization activities

---

## Contact Information

**Phone:** 8 (928) 022-21-40 (WhatsApp available)

**Email:** info@intelkavkaz.ru

**Address:** [To be confirmed] Grozny, Chechen Republic

**Social Media:** [Instagram, YouTube, Telegram — to be configured]

---

## Target Audience

- Residents of Chechen Republic and North Caucasus region
- Youth and students
- Educators and academics
- Community leaders
- Participants in intellectual and educational projects

---

## Site Structure & Content Pages

| Page | URL | Purpose |
|------|-----|---------|
| Home | `/` | Hero banner, latest news, key projects, mission statement |
| About | `/about` | Organization history, goals, mission, main activities |
| Leadership | `/leadership` | Chairman and leadership team information |
| Projects | `/projects` | List of ongoing and completed projects |
| Project Detail | `/projects/{slug}` | Detailed project information |
| News | `/news` | News, announcements, publications |
| News Detail | `/news/{slug}` | Full news article |
| Gallery | `/gallery` | Photos from events and projects |
| Documents | `/documents` | Charter, reports, official documents for download |
| Contact | `/contact` | Contact form, email, phone, address |
| Privacy Policy | `/privacy` | Personal data processing information |
| Terms of Service | `/terms` | Site usage rules |

---

## Design System

### Colors

- **Primary:** `#1F5F3B` (Mountain Green — nature, growth, stability, Caucasus landscape)
- **Secondary:** `#8B6B3F` (Earth Bronze — stone, heritage, traditional Caucasian motifs)
- **Accent:** `#2563EB` (Intelligence Blue — education, trust, innovation, knowledge)
- **Background:** `#F8F7F2` (Warm Ivory — clean, calm, paper-like)
- **Text:** `#1F2937` (Slate Gray — excellent readability)
- **Muted:** `#94A3B8` (Soft Slate)

### Typography

- **Headings:** Manrope, sans-serif
- **Body:** Inter, sans-serif
- **Monospace:** Fira Code

### Key UI Elements

- Base font size: 16px
- Button height: h-10
- Padding standard: px-4 py-2
- Components: Rounded buttons, underlined inputs, shadow-md cards with rounded-2xl corners

---

## Tech Stack (Same as NacSovet)

- **Frontend:** HTML, TailwindCSS, Alpine.js
- **Backend:** None (static site)
- **CMS:** None
- **Database:** Local JSON files (`/data` directory)
- **Hosting:** GitHub Pages or Timeweb
- **Versioning:** GitHub

---

## Key Customizations for IntelKavkaz

When redesigning NacSovet for IntelKavkaz, update:

1. **Organization Name & Branding**
   - Replace all references to "Национальный совет" with "Интеллектуальная Россия / Интеллектуальный Кавказ"
   - Use IntelKavkaz branding throughout

2. **Color Palette**
   - Use Mountain Green (#1F5F3B) as primary instead of current primary
   - Use Intelligence Blue (#2563EB) as accent instead of current accent
   - Update all Tailwind color tokens accordingly

3. **Contact & Leadership**
   - Update phone: 8 (928) 022-21-40
   - Update email: info@intelkavkaz.ru
   - Update chairman name: Мовлатов Лом-Али Ибрагимович
   - Update domain: intelkavkaz.ru

4. **Navigation & Pages**
   - Update site navigation to match IntelKavkaz page structure
   - Ensure all pages are properly routed

5. **Content Focus**
   - Adjust hero/mission messaging for intellectual community focus
   - Update project types to reflect educational initiatives
   - Align news categories with organization activities

---

## Notes

- Same Hugo blogging structure and functionality as NacSovet
- Same pagination, filtering, and search capabilities
- Only design and organizational details differ
- All technical infrastructure remains identical