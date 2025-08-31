📑 Divine Whispers – Frontend Requirement Document
1. General Design

Theme: Elegant mystic with modern web aesthetics.

Color Palette: Dark blue background, yellow highlights, white typography.

Typography: Bold headers, clean sans-serif for body.

Layout: Centered content, card-based sections, responsive (desktop + mobile).

Navigation: Top navigation bar (Home, Poem, Purchase, Account, Contact, Language Switch).

2. Pages & Features
2.1 Home Page

Hero Section

Large background image (fortune sticks / mystical theme).

Tagline text (e.g., “Hear the call of mystery guiding your true path.”).

CTA button: Learn More → scrolls or navigates to Poem selection.

Today’s Whisper Section

Sidebar widget: “Today’s Whisper” with button Try Now.

Clicking “Try Now” → random poem page.

2.2 Poem Selection Page

Choose Your Belief Section

Display multiple card options (e.g., Quan Yu, Yue Lao, Guanyin, etc.).

Each card contains image + name.

Clicking a card → leads to stick number selection page.

Stick Number Selection Page

Displays a grid of 1–100 (yellow cards).

Clicking a number → opens corresponding Poem Analysis page.

2.3 Poem Analysis Page

Header: Shows chosen deity image + name.

Poem Content Area:

Title, subtitle, fortune content (scroll/card style).

Tabs: “Original Poem”, “Explanation”, “Examples”.

Analysis Section

Displays basic interpretation (static).

Option for Deep Analysis → CTA button (consumes 5 coins).

After confirmation, deep analysis request is sent → result displayed in formatted Markdown text (AI-generated).

2.4 Deep Analysis Result Page

Layout: Markdown-rendered content block.

Content: Structured sections (question, answers, wisdom, guidance).

Style: White text on dark background, easy to read.

2.5 Purchase Page

Token Packages (3 card options):

5 Coins – $1

25 Coins – $4 (Most Popular)

100 Coins – $10 (Best Value)

Balance Display: Current coin balance at top of page.

CTA Button: “Purchase” → triggers payment flow.

2.6 Account Page

Features:

Login (Email, Password, Verification Code).

Register (same as above).

Reset password flow.

UI Style: Card-based form, simple, aligned with main theme.

2.7 Admin Dashboard (Restricted Access)

Overview: Users, active sessions, coin transactions, revenue.

Database Management:

Search poems.

Add / edit / delete poem entries.

Logs: User draw history, purchase history.

3. Technical Requirements

Framework: React + Tailwind CSS (or equivalent modern stack).

RWD: Must adapt for mobile, tablet, and desktop.

Animations:

Smooth transitions between pages.

Small animation for drawing fortune stick (optional).

Markdown Renderer: Required for deep analysis output.

Authentication: Email + password + verification code.

Payment Integration: For purchasing coins (API integration).

4. Components Summary

Header Navigation Bar

Hero Section with CTA

Whisper Widget (Today’s Whisper)

Belief Selection Card List

Stick Number Grid (1–100)

Poem Analysis Card

Deep Analysis CTA Button

Markdown Result Viewer

Coin Purchase Cards

Account Forms (Login/Register/Reset)

Admin Dashboard Panels