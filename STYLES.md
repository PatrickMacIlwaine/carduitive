# Carduitive - Design System & Styles Documentation

## Overview

This document outlines the design system, color palette, typography, and styling conventions used in the Carduitive application.

---

## Color Palette

### Primary Colors

| Name | Hex | CSS Variable | Usage |
|------|-----|--------------|-------|
| Primary Dark | `#09637E` | `hsl(193, 87%, 27%)` | Primary buttons, active states, main CTAs |
| Primary Light | `#7AB2B2` | `hsl(180, 28%, 58%)` | Accents, hover states, secondary highlights |
| Teal | `#088395` | `hsl(187, 89%, 31%)` | Links, icons, tertiary elements |
| Off-White | `#EBF4F6` | `hsl(195, 33%, 95%)` | Light mode backgrounds, card backgrounds |

### Dark Mode Colors

| Name | Hex | CSS Variable | Usage |
|------|-----|--------------|-------|
| Dark Background | `#0F172A` | `hsl(222, 47%, 8%)` | Dark mode page background |
| Dark Card | `#1E293B` | `hsl(222, 47%, 11%)` | Dark mode card backgrounds |
| Dark Muted | `#334155` | `hsl(222, 30%, 15%)` | Dark mode muted backgrounds |

### Semantic Colors

| Purpose | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | `hsl(195, 33%, 95%)` | `hsl(222, 47%, 8%)` |
| Foreground (Text) | `hsl(200, 50%, 15%)` | `hsl(195, 33%, 95%)` |
| Card Background | `hsl(195, 33%, 95%)` | `hsl(222, 47%, 11%)` |
| Muted Text | `hsl(200, 20%, 40%)` | `hsl(195, 20%, 60%)` |
| Border | `hsl(195, 20%, 85%)` | `hsl(222, 30%, 20%)` |
| Input Background | `hsl(195, 20%, 85%)` | `hsl(222, 30%, 20%)` |
| Ring (Focus) | `hsl(193, 87%, 27%)` | `hsl(180, 28%, 58%)` |
| Destructive | `hsl(0, 84%, 60%)` | `hsl(0, 62%, 30%)` |

---

## Typography

### Font Stack
- **Primary**: System UI font stack (Tailwind default)
- **Monospace**: Used for lobby codes (tracking-widest, uppercase)

### Type Scale

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| Hero | `text-4xl md:text-5xl` | `font-bold` | Page titles |
| H1 | `text-3xl md:text-4xl` | `font-bold` | Section headers |
| H2 | `text-2xl` | `font-bold` | Card titles |
| H3 | `text-xl` | `font-semibold` | Subsection headers |
| Body | `text-base` | `font-normal` | Paragraph text |
| Small | `text-sm` | `font-normal` | Descriptions, metadata |
| Tiny | `text-xs` | `font-normal` | Labels, badges |

### Lobby Code Typography
- **Font**: Monospace (inherited from system)
- **Size**: `text-lg`
- **Tracking**: `tracking-widest`
- **Transform**: `uppercase`
- **Example**: `ABCDE`

---

## Spacing System

### Layout Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `space-y-2` | 0.5rem | Tight vertical spacing |
| `space-y-4` | 1rem | Standard vertical spacing |
| `space-y-6` | 1.5rem | Section spacing |
| `space-y-8` | 2rem | Large section spacing |
| `gap-4` | 1rem | Grid/card gaps |
| `gap-6` | 1.5rem | Larger grid gaps |
| `p-4` | 1rem | Standard padding |
| `p-6` | 1.5rem | Card padding |

### Container
- **Max Width**: `max-w-7xl` (80rem / 1280px) for main layout
- **Max Width**: `max-w-3xl` (48rem / 768px) for content pages
- **Max Width**: `max-w-2xl` (42rem / 672px) for focused content
- **Horizontal Padding**: `px-4 sm:px-6 lg:px-8`

---

## Component Styles

### Buttons

#### Primary Button
```
Background: bg-primary (hsl(193, 87%, 27%))
Text: text-primary-foreground
Hover: hover:bg-primary/90
Size: h-9 px-4 py-2 (default)
Border Radius: rounded-md
```

#### Secondary/Ghost Button
```
Background: bg-transparent
Text: text-muted-foreground
Hover: hover:text-foreground hover:bg-accent
```

#### Large Button (CTA)
```
Height: h-12
Padding: px-8
Text: text-lg
```

### Cards

```
Background: bg-card
Border: border
Border Radius: rounded-xl
Shadow: shadow
Padding: p-6 (header/content)
```

#### Card Variants
- **Default**: Standard card with border
- **Hover Effect**: `group-hover:opacity-100` with gradient overlay
- **Featured**: `bg-primary/5 border-primary/20` for top 3 leaderboard

### Inputs

#### Text Input (Lobby Code)
```
Height: h-14
Text: text-2xl tracking-widest uppercase font-mono
Alignment: text-center
Border: border-input
Focus: focus-visible:ring-1 focus-visible:ring-ring
```

#### Standard Input
```
Height: h-9
Padding: px-3 py-1
Border: border-input
Border Radius: rounded-md
```

### Navigation

#### Navbar
```
Position: sticky top-0
Background: bg-card/50 backdrop-blur-sm
Border: border-b
Height: h-16
Z-Index: z-50
```

#### Nav Links
```
Active: bg-primary/10 text-primary
Inactive: text-muted-foreground hover:text-foreground hover:bg-accent
Padding: px-4 py-2
Border Radius: rounded-lg
```

---

## Dark Mode Implementation

### Strategy
- **Class-based**: Uses `.dark` class on `<html>` element
- **Storage**: Persists preference to localStorage
- **Default**: Respects system preference (`prefers-color-scheme`)

### Toggle Implementation
```typescript
// Uses useTheme hook
const { resolvedTheme, toggleTheme } = useTheme()

// Toggle button shows sun (dark mode) or moon (light mode)
{resolvedTheme === 'dark' ? <Sun /> : <Moon />}
```

### CSS Variables
Dark mode switches CSS custom properties:
```css
:root {
  --background: 195 33% 95%;    /* Light mode */
}

.dark {
  --background: 222 47% 8%;     /* Dark mode */
}
```

---

## Effects & Animations

### Transitions
```
Default: transition-colors
Duration: 150ms (standard), 200ms (emphasized)
Timing: ease-in-out
```

### Hover Effects
- **Cards**: `hover:bg-muted/50` or gradient overlay
- **Buttons**: `hover:bg-primary/90` or `hover:bg-accent`
- **Icons**: `group-hover:scale-105` or `group-hover:scale-110`

### Loading States
- **Spinner**: `animate-spin` with `Loader2` icon
- **Skeleton**: Use muted background with pulse animation

### Gradient Text
```
Background: bg-gradient-to-r from-carduitive-dark via-carduitive-teal to-carduitive-light
Clip: bg-clip-text
Text: text-transparent
```

### Framer Motion (Game Animations)

The game board uses `framer-motion` for animated interactions. Use `motion` components when:
- Elements enter the screen (player hands, opponent cards, results overlay)
- Cards are played or hovered
- Countdown or level transition animations

**Common patterns:**

```tsx
// Card deal-in
<motion.div
  initial={{ y: 20, opacity: 0 }}
  animate={{ y: 0, opacity: 1 }}
  transition={{ delay: index * 0.1 }}
>

// Card hover in hand
<motion.button
  whileHover={{ y: -30, scale: 1.15, zIndex: 20 }}
  whileTap={{ scale: 0.95 }}
>

// Overlay entrance
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
>
```

Use `transition-shadow` (CSS) for card shadows — avoid Framer Motion for simple shadow changes.

---

## Game Board Aesthetics

The game board uses a **card-game visual style** that intentionally differs from the main app theme. Playing cards use neutral white/slate tones to evoke physical cards rather than the app's teal palette.

### Playing Card (Face-up, Your Hand)
```
Background: bg-white
Border: border-2 border-slate-300
Border Radius: rounded-xl
Shadow: shadow-xl
Hover Border: hover:border-primary
Number: text-slate-800 font-bold
Corner Numbers: text-slate-400
```

### Playing Card (Face-down, Opponents)
```
Background: bg-slate-700 (connected) / bg-slate-500 (disconnected)
Border: border-2 border-slate-600
```

### Card Pile (Last Played)
```
Background: bg-white
Border: border-2 border-slate-200
Shadow: shadow-2xl
Size: w-28 h-40 md:w-36 md:h-52
```

### Player Connection Status
```
Connected: bg-green-500 indicator
Disconnected: bg-red-500 indicator + opacity-50 grayscale on hand
```

### Results Overlay
```
Backdrop: bg-background/95 (95% opaque)
Played cards: bg-slate-200 border-slate-300 text-slate-600
Remaining cards: bg-white border-primary/30 text-primary
Win action button: bg-green-500 hover:bg-green-600
Fail action button: bg-red-500 hover:bg-red-600
```

---

## Responsive Breakpoints

| Breakpoint | Width | Usage |
|------------|-------|-------|
| Default | < 640px | Mobile-first base styles |
| `sm:` | ≥ 640px | Small tablets |
| `md:` | ≥ 768px | Tablets |
| `lg:` | ≥ 1024px | Desktops |
| `xl:` | ≥ 1280px | Large desktops |

### Common Patterns
```
Grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3
Text: text-4xl md:text-5xl
Spacing: space-y-4 md:space-y-6
Padding: px-4 sm:px-6 lg:px-8
```

---

## Icon Usage

### Icon Library
- **Lucide React**: All icons from `lucide-react` package

### Common Icons
| Icon | Import | Usage |
|------|--------|-------|
| Trophy | `lucide-react` | Leaderboard, achievements |
| Medal | `lucide-react` | Rank 1-3 indicators |
| Award | `lucide-react` | Scores, badges |
| Users | `lucide-react` | Multiplayer, teams |
| Zap | `lucide-react` | Speed, energy |
| Plus | `lucide-react` | New game, add |
| ArrowRight | `lucide-react` | Navigation, submit |
| ArrowLeft | `lucide-react` | Back navigation |
| Sparkles | `lucide-react` | Logo, magic effects |
| Sun | `lucide-react` | Dark mode toggle (light) |
| Moon | `lucide-react` | Dark mode toggle (dark) |
| Home | `lucide-react` | Home navigation |
| Loader2 | `lucide-react` | Loading spinner |
| Gamepad2 | `lucide-react` | Game controls |

### Icon Sizes
- **Small (inline)**: `w-4 h-4`
- **Medium (buttons)**: `w-5 h-5`
- **Large (features)**: `w-6 h-6`
- **Extra Large (hero)**: `w-8 h-8`

---

## Best Practices

### DO
- Use Tailwind's utility-first approach
- Leverage `cn()` helper for conditional classes
- Use semantic color names (primary, secondary, destructive)
- Implement dark mode variants for all components
- Use responsive prefixes (md:, lg:) for layout changes
- Group related utilities together

### DON'T
- Don't hardcode hex values in components (use CSS variables)
- Don't mix arbitrary values without good reason
- Don't forget focus states for accessibility
- Don't use inline styles except for dynamic values
- Don't override component styles with !important

### Component Structure
```tsx
// Good: Utility classes grouped by concern
<div className={cn(
  "flex items-center gap-4",           // Layout
  "p-4 rounded-lg",                     // Spacing & Shape
  "bg-primary/5 border border-primary/20", // Colors
  "hover:bg-muted/50",                  // Interaction
  className                             // Overrides
)}>
```

---

## Files & Configuration

### Key Style Files
| File | Purpose |
|------|---------|
| `frontend/src/index.css` | Tailwind directives, CSS variables, base styles |
| `frontend/tailwind.config.ts` | Custom colors, theme extensions |
| `frontend/src/lib/utils.ts` | `cn()` helper for class merging |

### Tailwind Config Extensions
```typescript
// Custom colors
colors: {
  'carduitive': {
    dark: '#09637E',
    light: '#7AB2B2',
    teal: '#088395',
    white: '#EBF4F6',
  }
}

// Dark mode
darkMode: ['class']
```

---

## Accessibility

### Focus States
- All interactive elements have `focus-visible:ring-1 focus-visible:ring-ring`
- Ring color matches theme (primary in light, primary-light in dark)

### Color Contrast
- All text meets WCAG AA standards
- Muted text uses 60% opacity for hierarchy
- Destructive actions clearly distinguished

### Screen Readers
- Icons paired with text have `aria-hidden="true"`
- Icon-only buttons have `<span className="sr-only">` descriptions
- Navigation landmarks properly structured
