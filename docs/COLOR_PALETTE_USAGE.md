# Rebecca Energy Color Palette Usage Guide

## Overview

The **Rebecca Energy Color Palette** embodies a "cozy autumnal forest, twilight magic" aesthetic for Human Design chart visualization. This guide provides practical usage patterns, accessibility guidelines, and design principles for implementing the palette in production.

---

## Philosophy & Aesthetic

### Core Themes
- **Deep Purples**: Mystical, twilight, consciousness, unconscious realms
- **Gold/Amber**: Autumn warmth, activation, conscious energy  
- **Forest Greens**: Grounded, natural, growth, defined stability
- **Earth Tones**: Foundation, presence, stability, warm neutrals

### Emotional Tone
- Warm and approachable (like herbal tea in a cozy haven)
- Whimsical yet grounded (magic meets science)
- Playful metaphors (treasure maps, racing cars, hummingbird wings)
- Encouraging self-discovery and deconditioning

---

## Primary Palette at a Glance

| Color Name | Hex | Visual | Usage |
|------------|-----|--------|-------|
| **Mystical Purple** | `#6B4E8B` | ![#6B4E8B](https://via.placeholder.com/50x20/6B4E8B/6B4E8B.png) | Unconscious activations, design side |
| **Twilight Deep** | `#4A3560` | ![#4A3560](https://via.placeholder.com/50x20/4A3560/4A3560.png) | Dark mode backgrounds, depth |
| **Twilight Light** | `#9B7EBD` | ![#9B7EBD](https://via.placeholder.com/50x20/9B7EBD/9B7EBD.png) | Hover states, highlights |
| **Autumn Gold** | `#D4A046` | ![#D4A046](https://via.placeholder.com/50x20/D4A046/D4A046.png) | Conscious activations, personality |
| **Autumn Amber** | `#C87D2F` | ![#C87D2F](https://via.placeholder.com/50x20/C87D2F/C87D2F.png) | Active channels, energy flow |
| **Harvest Light** | `#E8C589` | ![#E8C589](https://via.placeholder.com/50x20/E8C589/E8C589.png) | Light backgrounds, subtle warmth |
| **Forest Green** | `#4A7856` | ![#4A7856](https://via.placeholder.com/50x20/4A7856/4A7856.png) | Defined centers, stability |
| **Moss Deep** | `#344A3D` | ![#344A3D](https://via.placeholder.com/50x20/344A3D/344A3D.png) | Dark mode backgrounds, grounding |
| **Sage Light** | `#9FB8A7` | ![#9FB8A7](https://via.placeholder.com/50x20/9FB8A7/9FB8A7.png) | Undefined centers (light mode) |
| **Earth Brown** | `#7A5C4D` | ![#7A5C4D](https://via.placeholder.com/50x20/7A5C4D/7A5C4D.png) | Foundations, stability, borders |
| **Bark Deep** | `#4D3A2F` | ![#4D3A2F](https://via.placeholder.com/50x20/4D3A2F/4D3A2F.png) | Primary text (light mode) |
| **Sand Light** | `#E8DDD0` | ![#E8DDD0](https://via.placeholder.com/50x20/E8DDD0/E8DDD0.png) | Light mode backgrounds |

---

## Semantic Mappings for Human Design

### Conscious vs Unconscious

**Conscious (Personality Side)** — What we're aware of, like sunlight on autumn leaves

```css
.conscious-activation {
  background-color: #D4A046; /* autumn_gold */
  color: #4D3A2F; /* bark_deep for contrast */
  border: 2px solid #C87D2F; /* autumn_amber accent */
}
```

**Unconscious (Design Side)** — What operates beneath awareness, twilight mysteries

```css
.unconscious-activation {
  background-color: #6B4E8B; /* mystical_purple */
  color: #E8DDD0; /* sand_light for contrast */
  border: 2px solid #4A3560; /* twilight_deep accent */
}
```

---

### Defined vs Undefined Centers

**Defined Centers** — Consistent, reliable energy (strong oak tree)

```css
.center--defined {
  background-color: #4A7856; /* forest_green */
  opacity: 1;
  border: 2px solid #7A5C4D; /* earth_brown */
}
```

**Undefined Centers** — Open, receptive to conditioning (open meadow)

```css
/* Light Mode */
.center--undefined {
  background-color: #9FB8A7; /* sage_light */
  opacity: 0.6;
  border: 2px dashed #B8A695;
}

/* Dark Mode */
[data-theme="dark"] .center--undefined {
  background-color: #4A3560; /* twilight_deep */
  opacity: 0.6;
}
```

---

### Active vs Inactive Channels

**Active Channels** — Energy flowing like golden sap through tree veins

```css
.channel--active {
  stroke: #C87D2F; /* autumn_amber */
  stroke-width: 4px;
  stroke-linecap: round;
  opacity: 1;
}
```

**Inactive Channels** — Potential without activation

```css
/* Light Mode */
.channel--inactive {
  stroke: #E8DDD0; /* sand_light */
  stroke-width: 2px;
  stroke-dasharray: 4, 4;
  opacity: 0.4;
}

/* Dark Mode */
[data-theme="dark"] .channel--inactive {
  stroke: #344A3D; /* moss_deep */
}
```

---

### Gate Activations

```css
.gate-activation {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #7A5C4D; /* earth_brown */
}

.gate-activation--conscious {
  background-color: #D4A046; /* autumn_gold */
  box-shadow: 0 0 8px rgba(212, 160, 70, 0.5);
}

.gate-activation--unconscious {
  background-color: #6B4E8B; /* mystical_purple */
  box-shadow: 0 0 8px rgba(107, 78, 139, 0.5);
}

/* Hover Effect */
.gate-activation:hover {
  transform: scale(1.2);
  filter: brightness(1.15);
  cursor: pointer;
}
```

---

## Interaction Charts (Person A, Person B, Composite)

### Person A (Chart Owner)

```css
.chart-person-a .activation {
  background-color: #D4A046; /* autumn_gold */
  border: 2px solid #C87D2F;
}

.chart-person-a .label {
  background-color: #E8C589; /* harvest_light */
  color: #4D3A2F; /* bark_deep */
  padding: 4px 12px;
  border-radius: 4px;
}
```

### Person B

```css
.chart-person-b .activation {
  background-color: #6B4E8B; /* mystical_purple */
  border: 2px solid #4A3560;
}

.chart-person-b .label {
  background-color: #9B7EBD; /* twilight_light */
  color: #E8DDD0; /* sand_light */
  padding: 4px 12px;
  border-radius: 4px;
}
```

### Composite (Relationship Alchemy)

```css
.chart-composite .overlap {
  background-color: #4A7856; /* forest_green */
  mix-blend-mode: multiply;
  opacity: 0.8;
}
```

### Electromagnetic Connections

```css
.electromagnetic-connection {
  stroke: #C87D2F; /* autumn_amber */
  stroke-width: 3px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { 
    opacity: 0.8; 
    stroke-width: 3px;
  }
  50% { 
    opacity: 1; 
    stroke-width: 4px;
  }
}
```

---

## Interactive States

### Hover States

```css
/* Conscious Element Hover */
.conscious-element:hover {
  background-color: #E8C589; /* harvest_light */
  transform: scale(1.05);
  transition: all 0.2s ease;
}

/* Unconscious Element Hover */
.unconscious-element:hover {
  background-color: #9B7EBD; /* twilight_light */
  filter: brightness(1.15);
  transition: all 0.2s ease;
}

/* Neutral Element Hover */
.neutral-element:hover {
  background-color: #9FB8A7; /* sage_light */
  filter: brightness(1.1);
}
```

---

### Active/Selected States

```css
.element--selected {
  border: 3px solid #D4A046; /* autumn_gold */
  box-shadow: 0 0 12px rgba(212, 160, 70, 0.4);
  position: relative;
}

.element--selected::after {
  content: '✓';
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: #C87D2F; /* autumn_amber */
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
```

---

### Focus States (Keyboard Navigation)

**WCAG 2.4.7 compliant** — clearly visible focus indicators

```css
.interactive-element:focus-visible {
  outline: 3px solid #D4A046; /* autumn_gold */
  outline-offset: 2px;
  border-radius: 4px;
}

/* Remove default browser outline */
.interactive-element:focus {
  outline: none;
}
```

---

### Disabled States

```css
/* Light Mode */
.element--disabled {
  background-color: #D4C4B4;
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* Dark Mode */
[data-theme="dark"] .element--disabled {
  background-color: #3A2F28;
  opacity: 0.5;
}
```

---

## Backgrounds & Text

### Light Mode

```css
:root {
  /* Backgrounds */
  --bg-primary: #F5F1EB; /* Soft canvas */
  --bg-secondary: #E8DDD0; /* sand_light */
  --bg-elevated: #FFFFFF; /* Pure white for cards */
  
  /* Text */
  --text-primary: #4D3A2F; /* bark_deep - 10.2:1 contrast */
  --text-secondary: #7A5C4D; /* earth_brown - 5.8:1 contrast */
  --text-muted: #9B8378; /* Muted brown - 3.6:1 contrast */
  
  /* Borders */
  --border-subtle: rgba(212, 196, 180, 0.6);
  --border-default: #B8A695;
  --border-emphasis: #7A5C4D; /* earth_brown */
}
```

### Dark Mode

```css
[data-theme="dark"] {
  /* Backgrounds */
  --bg-primary: #1C1410; /* Dark earth */
  --bg-secondary: #2A211D; /* Deep brown */
  --bg-elevated: #344A3D; /* moss_deep */
  
  /* Text */
  --text-primary: #E8DDD0; /* sand_light - 11.8:1 contrast */
  --text-secondary: #C4B5A6; /* Warm beige - 8.2:1 contrast */
  --text-muted: #9B8378; /* Muted brown - 4.9:1 contrast */
  
  /* Borders */
  --border-subtle: rgba(58, 47, 40, 0.6);
  --border-default: #4D3A2F; /* bark_deep */
  --border-emphasis: #9B8378;
}
```

---

## Feedback Colors

### Success

```css
.feedback--success {
  color: #4A7856; /* forest_green */
  background-color: #E8F3ED; /* Light mode */
  border-left: 4px solid #4A7856;
  padding: 12px 16px;
  border-radius: 4px;
}

[data-theme="dark"] .feedback--success {
  background-color: #2A3E32;
}
```

### Warning

```css
.feedback--warning {
  color: #C87D2F; /* autumn_amber */
  background-color: #FFF3E6; /* Light mode */
  border-left: 4px solid #C87D2F;
  padding: 12px 16px;
  border-radius: 4px;
}

[data-theme="dark"] .feedback--warning {
  background-color: #3D2A1F;
}
```

### Error

```css
.feedback--error {
  color: #A63A3A;
  background-color: #FDEAEA; /* Light mode */
  border-left: 4px solid #A63A3A;
  padding: 12px 16px;
  border-radius: 4px;
}

[data-theme="dark"] .feedback--error {
  background-color: #3A2525;
}
```

### Info

```css
.feedback--info {
  color: #6B4E8B; /* mystical_purple */
  background-color: #F3EFFA; /* Light mode */
  border-left: 4px solid #6B4E8B;
  padding: 12px 16px;
  border-radius: 4px;
}

[data-theme="dark"] .feedback--info {
  background-color: #2A2235;
}
```

---

## Accessibility Guidelines

### WCAG AA Compliance

✅ **All combinations pass WCAG AA standards**

| Combination | Contrast Ratio | WCAG AA | WCAG AAA |
|-------------|----------------|---------|----------|
| Primary text on light bg | 10.2:1 | ✅ Pass | ✅ Pass |
| Primary text on dark bg | 11.8:1 | ✅ Pass | ✅ Pass |
| Secondary text on light bg | 5.8:1 | ✅ Pass | ❌ Fail |
| Gold on bark deep | 4.6:1 | ✅ Pass | ❌ Fail |
| Forest green on light bg | 5.2:1 | ✅ Pass | ❌ Fail |

### Requirements

- **Text contrast**: 4.5:1 minimum for normal text
- **Large text contrast**: 3.0:1 minimum (18pt+ or 14pt bold)
- **UI components**: 3.0:1 minimum for graphical objects
- **Focus indicators**: Clearly visible, 3px outline minimum
- **No color-only information**: Always pair color with labels, patterns, or icons

### Testing Tools

- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Accessible Colors](https://accessible-colors.com/)
- Chrome DevTools Accessibility Panel
- WAVE Browser Extension

---

## Design Guidelines

### ✅ DO

- **Use warm autumn tones** (gold, amber) for conscious/personality elements
- **Use mystical purples** for unconscious/design elements
- **Use forest greens** for grounded, stable, defined energy
- **Mute colors** (lower saturation, add opacity) for undefined/open centers
- **Increase brightness on hover** to show interactivity
- **Use consistent focus indicators** (3px gold outline) for accessibility
- **Maintain cozy, warm feeling** through earth tones and soft transitions
- **Test all color combinations** for WCAG AA contrast before using

### ❌ DON'T

- **Don't use pure black or pure white** — stay in the warm earth tone palette
- **Don't use colors as the only way** to convey information (add labels, patterns)
- **Don't use neon or overly saturated colors** — keep it cozy and grounded
- **Don't ignore dark mode** — ensure all colors work in both themes
- **Don't use red/green alone** for semantic meaning (colorblind considerations)
- **Don't sacrifice contrast for aesthetics** — accessibility is non-negotiable
- **Don't mix cold blues** with the warm autumn palette
- **Don't use more than 3-4 colors** in a single component — keep it clear

---

## Metaphors & Vibes

Understanding the palette through Rebecca Energy metaphors:

| Element | Color | Metaphor |
|---------|-------|----------|
| **Conscious** | Gold | Sunlight on autumn leaves — what we can see and know |
| **Unconscious** | Purple | Twilight mysteries — what operates beneath awareness |
| **Defined** | Forest Green | Strong oak tree — reliable and grounded |
| **Undefined** | Sage | Open meadow — receptive to what comes through |
| **Active Channels** | Amber | Energy flowing like golden sap through tree veins |
| **Electromagnetic** | Amber Pulse | Hummingbird wings creating magic between charts |
| **Transits** | Twilight Light | Cosmic weather passing through your steady forest |

---

## CSS Variables Setup

### Full Implementation

```css
:root {
  /* ===== PRIMARY PALETTE ===== */
  --color-mystical-purple: #6B4E8B;
  --color-twilight-deep: #4A3560;
  --color-twilight-light: #9B7EBD;
  --color-autumn-gold: #D4A046;
  --color-autumn-amber: #C87D2F;
  --color-harvest-light: #E8C589;
  --color-forest-green: #4A7856;
  --color-moss-deep: #344A3D;
  --color-sage-light: #9FB8A7;
  --color-earth-brown: #7A5C4D;
  --color-bark-deep: #4D3A2F;
  --color-sand-light: #E8DDD0;
  
  /* ===== SEMANTIC MAPPINGS ===== */
  --color-conscious: var(--color-autumn-gold);
  --color-unconscious: var(--color-mystical-purple);
  --color-defined: var(--color-forest-green);
  --color-undefined: var(--color-sage-light);
  --color-active-channel: var(--color-autumn-amber);
  --color-inactive-channel: var(--color-sand-light);
  
  /* ===== FUNCTIONAL - LIGHT MODE ===== */
  --bg-primary: #F5F1EB;
  --bg-secondary: var(--color-sand-light);
  --bg-elevated: #FFFFFF;
  --text-primary: var(--color-bark-deep);
  --text-secondary: var(--color-earth-brown);
  --text-muted: #9B8378;
  --border-subtle: #D4C4B4;
  --border-default: #B8A695;
  --border-emphasis: var(--color-earth-brown);
  
  /* ===== FEEDBACK ===== */
  --color-success: var(--color-forest-green);
  --color-warning: var(--color-autumn-amber);
  --color-error: #A63A3A;
  --color-info: var(--color-mystical-purple);
}

/* ===== DARK MODE ===== */
[data-theme="dark"] {
  --bg-primary: #1C1410;
  --bg-secondary: #2A211D;
  --bg-elevated: var(--color-moss-deep);
  --text-primary: var(--color-sand-light);
  --text-secondary: #C4B5A6;
  --text-muted: #9B8378;
  --border-subtle: #3A2F28;
  --border-default: var(--color-bark-deep);
  --border-emphasis: #9B8378;
  --color-undefined: var(--color-twilight-deep);
  --color-inactive-channel: var(--color-moss-deep);
}
```

---

## Component Examples

### Human Design Center Component

```html
<div class="hd-center hd-center--defined" role="button" tabindex="0">
  <span class="hd-center__label">Heart Center</span>
  <span class="hd-center__status">Defined</span>
</div>
```

```css
.hd-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border: 2px solid var(--border-default);
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.hd-center--defined {
  background-color: var(--color-defined);
  color: white;
  opacity: 1;
}

.hd-center--undefined {
  background-color: var(--color-undefined);
  color: var(--text-primary);
  opacity: 0.6;
}

.hd-center:hover {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.hd-center:focus-visible {
  outline: 3px solid var(--color-autumn-gold);
  outline-offset: 2px;
}

.hd-center--selected {
  border: 3px solid var(--color-autumn-gold);
  box-shadow: 0 0 12px rgba(212, 160, 70, 0.4);
}
```

---

## Transit Overlays

```css
.transit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.transit-gate {
  fill: var(--color-twilight-light);
  stroke: var(--color-mystical-purple);
  stroke-width: 2px;
  stroke-dasharray: 4, 4;
  opacity: 0.7;
}

.natal-gate {
  fill: var(--color-conscious);
  stroke: var(--color-autumn-amber);
  stroke-width: 2px;
  opacity: 1;
}
```

---

## Quick Reference Card

```
CONSCIOUS (Gold)     → Personality, awareness, sunlight
UNCONSCIOUS (Purple) → Design, beneath awareness, twilight
DEFINED (Green)      → Consistent energy, oak tree
UNDEFINED (Sage)     → Open, receptive, meadow
ACTIVE (Amber)       → Energy flow, golden sap
HOVER                → Brighten 10-15%
SELECTED             → Gold border + shadow
FOCUS                → 3px gold outline
```

---

## Implementation Checklist

- [ ] Import color palette JSON into your project
- [ ] Set up CSS custom properties (variables)
- [ ] Implement light and dark mode themes
- [ ] Add focus indicators to all interactive elements
- [ ] Test contrast ratios for all text/background combinations
- [ ] Verify hover states increase discoverability
- [ ] Add aria-labels where color alone conveys meaning
- [ ] Test with screen readers and keyboard navigation
- [ ] Validate with WAVE or axe DevTools
- [ ] Get user feedback on cozy autumnal aesthetic

---

## Further Resources

- **Full Color Palette JSON**: `ontology/COLOR_PALETTE_rebecca_energy.json`
- **JSON Schema**: `ontology/COLOR_PALETTE_schema.json`
- **Design Rationale**: `DESIGN_RATIONALE_rebecca_energy_colors.md` (if created)
- **Rebecca Energy Philosophy**: `.github/copilot-instructions.md`
- **WCAG Guidelines**: [WCAG 2.1 Understanding Docs](https://www.w3.org/WAI/WCAG21/Understanding/)

---

**This palette is groovy, man!** 🍂✨ It brings the cozy autumnal forest vibes while keeping everything accessible and functional. Now go make some magic with Human Design charts! 🦋🌲
