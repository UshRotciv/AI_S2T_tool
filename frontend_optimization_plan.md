# Frontend Optimization Plan

## 1. Objective

The primary goal is to enhance the user experience of the `confidential-expert-ai` frontend. This will be achieved by redesigning the scenario browsing interface to be more intuitive, visually appealing, and interactive, drawing inspiration from the existing admin panel's card layout.

## 2. Analysis of Current State

- The `HomePage.tsx` currently displays scenarios in a simple vertical list using the `ScenarioCard.tsx` component.
- Each card displays its full content by default, which can be overwhelming if there are many scenarios.
- The layout is functional but lacks the visual organization and interactivity required for a modern, user-friendly knowledge base.

## 3. Proposed Implementation Plan

This plan is divided into three phases:

### Phase 1: Refactor `ScenarioCard.tsx` for Interactivity

The core of the change lies in making the scenario cards expandable and collapsible.

- **State Management:**
  - Add a local state `isExpanded` to `ScenarioCard.tsx` to toggle the card's view.
- **Collapsed View (Default):**
  - Display only the scenario `title` and `category`.
  - Add a clear visual indicator (e.g., a "+" icon or a chevron arrow) to show that the card is clickable.
- **Expanded View (On Click):**
  - Reveal the full details: `question`, `answer`, and `learnings`.
  - The visual indicator should change (e.g., to a "-" icon or an upward-pointing chevron).
- **Styling:**
  - Apply a card-like style with borders, box-shadow, and padding, similar to the `.admin-card` but with a more polished, user-facing design.
  - Use smooth CSS transitions for the expansion/collapse animation to create a fluid user experience.

### Phase 2: Update `HomePage.tsx` Layout

The main page will be updated to arrange the new interactive cards in a responsive grid.

- **Layout System:**
  - Modify the `.scenarios-list` container in `App.css` to use CSS Grid (`display: grid`).
  - Configure the grid to be responsive:
    - On large screens, display 2-3 cards per row (`grid-template-columns: repeat(auto-fill, minmax(350px, 1fr))`).
    - On smaller screens (mobile), it will automatically adjust to a single-column layout.
- **Component Integration:**
  - No major changes are needed in the `HomePage.tsx` logic, as the expansion/collapse behavior is encapsulated within each `ScenarioCard.tsx`.

### Phase 3: Visual & User Experience Enhancements

These changes will improve scannability and visual appeal.

- **Color-Coded Categories:**
  - Assign a unique, subtle color to each scenario `category`.
  - This can be implemented as a colored left border or a light background tint on the card. A helper function will map category names to specific colors.
  - **Example Categories & Colors:**
    - `General`: Light Blue (`#e7f3ff`)
    - `Development`: Light Green (`#e6fffa`)
    - `Data Security`: Light Orange (`#fff4e6`)
    - `Network`: Light Purple (`#f3e8ff`)
- **Improved Typography:**
  - Increase the font size and weight of the card `title` to make it stand out.
  - Use distinct styling for `question`, `answer`, and `learnings` to create a clear visual hierarchy within the expanded card.
- **Search and Filter Interaction:**
  - When a user searches, the grid of cards will dynamically and smoothly filter to show only the relevant results. The grid layout will automatically re-flow the visible cards.
