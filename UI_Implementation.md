# TASK: UI/UX Overhaul, Kinetic Warm-Editorial Landing Page, Metric Tooltips & State Fixes

## Role & Goal
You are a senior full-stack engineer and creative technologist specializing in Next.js (App Router), Tailwind CSS, Framer Motion / GSAP, and robust React state architecture. Your objective is to:
1. Rebuild the public landing/about homepage into a high-end, kinetic editorial experience using a warm, visually appetizing modern light palette with dynamic scroll choreography and tactile hover micro-interactions (inspired by premier creative development studios like OFF+BRAND).
2. Replace all generic default blue accents across the entire application with an elevated palette (deep forest/emerald green and sharp obsidian charcoal).
3. Add explanatory (i) calculation tooltips to every dashboard metric.
4. Eliminate developer-facing backend jargon, decouple form actions, fix input scroll bugs, and implement an inline cleaned-data viewer with full session security.

---

## 1. Visual Design Tokens (Modern Warm Editorial & Emerald)

Replace all default blue and dark-only styling across global CSS and Tailwind configs with a warm, tactile palette:

a. Canvas & Surfaces:
   1. Base Background: Warm Alabaster / Oatmeal (`#F9F9F6` or `#F5F5F0`)
   2. Surface Cards: Crisp Studio White (`#FFFFFF`) with subtle warm stone borders (`border-stone-200` / `#E7E5E4`) and soft layered elevation (`shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]`)
b. Typography & Ink:
   1. Primary Text: Deep Obsidian / Charcoal (`#18181B` / `#09090B`)
   2. Body / Secondary: Warm Slate / Muted Stone (`#52525B` / `#71717A`)
c. Accent & Focal Points (Replacing Default Blue):
   1. Primary Action: Deep Botanical Forest / Emerald (`#064E3B` / `#0F4C3A`)
   2. Highlights & Badges: Vibrant Sage / Mint tint (`#ECFDF5` background with `#047857` border and text)
   3. Secondary Contrast: Sharp Obsidian Black (`#09090B`) for high-contrast pills and dark interactive elements

---

## 2. Kinetic Editorial Landing & About Us Page (`/` or `/about`)

Build an interactive, smooth-scrolling editorial landing page featuring fluid scroll-linked animations, text reveals, and interactive tab micro-interactions.

### Motion & Interaction Guidelines
a. Smooth Inertia Scroll: Wrap the landing route with Lenis smooth scroll (`lenis/react`).
b. Scroll Choreography (GSAP ScrollTrigger or Framer Motion):
   1. Kinetic split-text hero reveal (masked lines sliding up smoothly on entry).
   2. Scroll-linked parallax cards and dynamic image scale clips (`clip-path` expanding reveals).
   3. Subtle floating sticker/badge physics that respond to scroll velocity.
c. Interactive Navigation & Hover Tabs:
   1. Dynamic magnetic pill cursor / sliding background indicator: when hovering across nav items or section tabs, a smooth highlight capsule slides and morphs behind the active tab (using Framer Motion `layoutId="tab-indicator"` or GSAP FLIP).
   2. Interactive tilt & magnetic pull on primary buttons and cards.

### Required Page Sections
1. Header: Clean editorial typography, morphing hover nav anchors (`About`, `Privacy & Security`, `Financial Insights`), and dual auth actions:
   a. "Log In": Minimalist ghost button (`text-stone-800 hover:bg-stone-200/60 transition-colors`) redirecting to `/login`.
   b. "Get Started": Solid emerald capsule button (`bg-emerald-900 text-white hover:bg-emerald-800 shadow-sm hover:scale-[1.02] transition-all`) redirecting to `/signup`.
2. Hero Section: Bold editorial display typography, animated kinetic value statement, dynamic interactive badge, and immediate call-to-action triggers.
3. About Us Narrative: Multi-column editorial storytelling presenting financial intelligence, precision data structuring, and clarity.
4. Security & Privacy Bento Grid: Interactive hover-reveal cards breaking down private local-session processing, client-side isolation, and bank-grade encryption.
5. Financial Insights / Blog: Dynamic cards with category pill tags, hover-scaling preview imagery, and clean reading-time indicators.
6. Editorial Footer: Minimalist sitemap, regulatory notes, and copyright details on a soft warm stone canvas (`#EFEFEA`).

---

## 3. Dashboard Metric Calculation Tooltips (`(i)` Info Triggers)

Every key financial metric displayed on the dashboard (e.g., Net Worth, Savings Rate, Cash Flow, Burn Rate, Goal Projections, Allocation %):
1. Add a concise `(i)` info icon right next to the metric title label.
2. Hover / Focus Behavior: Opens an accessible, lightweight tooltip explaining the exact formula or logic in clear, human terms without backend jargon.
   a. Example (Savings Rate): `"Calculated as (Monthly Income − Total Expenses) ÷ Monthly Income × 100."`
   b. Example (Net Worth): `"Total verified bank & investment balances minus active liabilities."`
   c. Example (Runway / Burn Rate): `"Total liquid savings divided by average monthly spend over the last 3 months."`

---

## 4. Authentication & Session Flow
1. Logout on Browser Refresh:
   a. Store auth session tokens exclusively in session-only memory or `sessionStorage` (or trigger an explicit logout on window unload/mount) so hard refreshing clears active session tokens and returns the user to `/login`.
2. Post-Signup Redirect:
   a. When a user creates an account, immediately route them to the input data page (`/input-data` or `/dashboard/input`).
3. Trust & Security Onboarding Dialog:
   a. On first arrival to the input data page post-signup, trigger a clear 3-card modal titled "How We Protect & Process Your Financial Data":
      1. Card 1: Private & Isolated: Encrypted in transit; data never leaves your secure session.
      2. Card 2: Smart Financial Structuring: Simple explanation of how your CSV/CAS statements are automatically normalized into readable summaries without exposing raw transaction trails.
      3. Card 3: 100% User Control: Retain complete control with one-click permanent deletion anytime.
   b. Provide a clean "Continue to Dashboard" dismiss button with an option to silence the prompt for that session.

---

## 5. UI Copy Sanitization & Technical Polish
1. Eliminate Developer & Internal Jargon:
   a. Audit all dashboard copy, file upload progress bars, and status cards.
   b. Remove references to backend execution steps, agent orchestration chains, database schemas, and parsing pipelines.
   c. Replace with customer-focused terminology (e.g., replace *"Agent 2 parsing CSV schemas"* with *"Organizing your transactions..."*).
2. Hover Info ("i") Tooltips for Column Formatting:
   a. Remove long descriptive paragraphs explaining how columns are converted during upload.
   b. Replace with a subtle `(i)` tooltip icon next to column headers: *"Automatically categorized to standard financial formats."*

---

## 6. Component Fixes & State Management

a. Number Input Scroll Lock:
   1. Prevent accidental value increments/decrements when scrolling over money inputs (e.g., in "Add Bank" or "Add Goals").

b. Decouple "Save Account" & "Save Goals":
   1. Isolate form submit handlers and state boundaries so clicking "Save Account" executes only the account mutation, leaving goal validation and mutation untouched (and vice versa).

c. Inline "View Cleaned Data" Drawer & Close Action:
   1. Issue: Cleaned data container currently expands at the bottom of the page.
   2. Fix: Render the expanded data container directly underneath the trigger element as an inline collapsible accordion.
   3. Place a visible "Close" (✕) button at the top-right of the expanded container to collapse it instantly.

d. Cleaned CSV Table Redesign (Modern Warm Light Style):
   1. Redesign the table into a clean, legible data grid:
   2. Header row: `bg-stone-100 text-stone-600 text-xs font-medium uppercase tracking-wider`.
   3. Rows: `bg-white hover:bg-stone-50 border-b border-stone-100 transition-colors`.
   4. Numbers/Amounts: Right-aligned tabular monospace font (`font-mono text-stone-900`).
   5. Status badges: Pill tags using emerald/sage tones (`bg-emerald-50 text-emerald-700 border border-emerald-200`).

e. Delete CSV / Clear Context Action:
   1. Add an explicit "Delete File" / "Clear Data" action button.
   2. Upon confirmation:
      * Purge the active dataset from client state and session context.
      * Trigger backend context removal so the file is no longer referenced in active analysis.

---

## 7. Execution Order

1. Palette & Tokens: Replace default blues across global CSS and Tailwind config with the warm alabaster, stone, and emerald palette.
2. Functional State Fixes: Apply number input scroll locks, separate account/goal save triggers, and enforce session-refresh logout behavior.
3. Data Input & Metric Tooltips: Build the inline collapsible cleaned-data accordion with the close/delete actions, add (i) calculation tooltips across all dashboard metrics, and sanitize all technical copy.
4. Security Modal: Implement the 3-card onboarding modal on the data input route.
5. Kinetic Landing Page: Implement Lenis smooth scrolling, scroll-triggered section reveals, and sliding/morphing tab hover indicators.