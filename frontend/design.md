---
version: 1.0.0
name: Northline Visual System
description: A visual language defined by deep blacks, high-contrast typography, and cinematic orange accents.
colors:
  background: "#090909"
  surface: "#101010"
  accent: "#f04a23"
  accent-hover: "#ff5b32"
  text-primary: "#f4f1ea"
  text-secondary: "#ffffffa6"
  text-muted: "#ffffff73"
  light-surface: "#e9e3d8"
  light-text: "#11100e"
typography:
  display:
    family: "Manrope, sans-serif"
    weights: [400, 500, 600]
    tracking: "-0.025em"
  body:
    family: "Inter, sans-serif"
    weights: [400, 500, 600]
    lineHeight: "1.75"
spacing:
  xs: "4px"
  sm: "12px"
  md: "20px"
  lg: "32px"
  xl: "80px"
  section: "112px"
rounded:
  sm: "2px"
  md: "6px"
  lg: "12px"
  full: "999px"
components:
  navigation:
    height: "80px"
    background: "transparent"
    blur: "24px"
    stickyZIndex: "50"
  buttons:
    padding: "12px 24px"
    fontSize: "14px"
    transition: "200ms cubic-bezier(.22,.61,.36,1)"
  cards:
    aspectRatio: "16/10"
    hoverScale: "1.03"
    transition: "700ms"
  faq:
    itemPadding: "24px 0px"
    transition: "200ms ease"
motion:
  reveal:
    duration: "700ms"
    easing: "cubic-bezier(.22,.61,.36,1)"
    yOffset: "1.5rem"
---
## Overview
Northline is built on the principle of "visual tension." It uses a dark-mode-first approach to prioritize media assets, paired with a singular high-energy accent color (#f04a23) to drive conversion. The system transitions into a light "sand" theme for process-heavy sections to maintain legibility and professional contrast.

## Colors
The palette is rooted in #090909 to mimic a cinema environment. Text uses an off-white (#f4f1ea) to reduce harsh contrast glare. The primary brand color is a high-saturation orange-red used sparingly for focus points, call-to-actions, and interactive state indicators.

## Typography
- **Display (Manrope):** Used for headlines and numeric callouts. Characterized by tight tracking and variable weights to create visual hierarchy in cinematic layouts.
- **Body (Inter):** Used for functional text and descriptors. Optimized for readability against dark backgrounds with a generous 1.75 line height.

## Spacing
The system utilizes a generous spacing scale to allow visual assets to "breathe." Section vertical padding is standardized at 80px (sm) to 112px (lg). Grid gutters follow a standard 10-column or 12-column responsive layout.

## Layout
Layouts prioritize the 12-column grid. Key elements utilize absolute positioning for "Scroll to Explore" indicators and floating navigation. The system frequently uses `overflow-x-hidden` to prevent horizontal shifts during entrance animations and scales.

## Elevation & Depth
Depth is achieved through layering rather than shadows:
- **Background Layer:** Media with linear gradients (to bottom/top) for text legibility.
- **Midground Layer:** Component surfaces with 10-15% white opacity.
- **Foreground Layer:** Floating navigation with backdrop-blur (XL) and 90-95% opacity.
- **Z-Index Scale:** Header (50), Mobile Menu (absolute top-full), Skip Link (100).

## Shapes
Rectilinear forms dominate, softened by a standard 6px (md) corner radius on cards and buttons. Full rounding (999px) is reserved for small status indicators and pill-shaped badges.

## Components
- **Hero:** Full-bleed background imagery with a scale(1.03) transform and a dark gradient overlay (linear-gradient top/bottom).
- **Work Cards:** Aspect-ratio locked (16/10 or 4/5) containers with internal image scaling on hover and top-right icon overlays.
- **Process Grid:** 3-column layout with border-r/border-b separators (15% opacity) creating a structured, technical feel.
- **Pricing Articles:** Grid-based rows with 33%/50% width distribution and right-aligned pricing tiers.
- **FAQ Accordion:** Grid-row transition (0fr to 1fr) for smooth CSS-only height expansion.

## Motion
Motion is purposeful and "weighty."
- **Scroll Reveals:** Intersection Observer triggers a translateY(0) and blur(0) with a 700ms duration.
- **Hero Parallax:** Media background moves at 10% of scroll speed (0.1px per pixel scrolled).
- **Button Interaction:** Color shifts and arrow icons translate-x on hover to signal direction.

## Do's and Don'ts
### Do's
- Use high-quality, cinematic photography with warm or directional lighting.
- Keep navigation links semi-transparent (65%) until hovered.
- Use the "sand" background (#e9e3d8) for instructional or text-heavy technical sections.

### Don'ts
- Do not use shadows or heavy glows; rely on contrast and borders for definition.
- Avoid using the brand orange for large background areas; it is an accent only.
- Do not exceed 3 levels of nested typographic hierarchy per section.

## Accessibility
- **Focus States:** High-visibility focus rings in #f04a23 with a 4px offset.
- **Contrast:** Maintain AA compliance for all body text against dark backgrounds.
- **Motion Control:** Respect `prefers-reduced-motion` by forcing opacity to 1 and removing transforms.
- **Navigation:** Include a skip-to-content link positioned fixed-top for keyboard users.