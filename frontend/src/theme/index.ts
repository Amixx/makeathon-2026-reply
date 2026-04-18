/** Typed token exports — values are CSS variable references */

export const colors = {
  // Backgrounds
  bgDefault: 'var(--bg-default)',
  bgCard: 'var(--bg-card)',
  bgMuted: 'var(--bg-muted)',
  bgInverted: 'var(--bg-inverted)',
  bgInvertedCard: 'var(--bg-inverted-card)',
  bgInvertedMuted: 'var(--bg-inverted-muted)',

  // Borders
  borderDefault: 'var(--border-default)',
  borderMuted: 'var(--border-muted)',
  borderStrong: 'var(--border-strong)',
  borderInverted: 'var(--border-inverted)',

  // Foregrounds
  fgDefault: 'var(--fg-default)',
  fgMuted: 'var(--fg-muted)',
  fgInverted: 'var(--fg-inverted)',
  fgInvertedMuted: 'var(--fg-inverted-muted)',
  fgInvertedAccent: 'var(--fg-inverted-accent)',
  fgAccent: 'var(--fg-accent)',

  // Accent (coral)
  accent50: 'var(--accent-50)',
  accent100: 'var(--accent-100)',
  accent200: 'var(--accent-200)',
  accent300: 'var(--accent-300)',
  accent400: 'var(--accent-400)',
  accent500: 'var(--accent-500)',
  accent600: 'var(--accent-600)',
  accent700: 'var(--accent-700)',
  accent800: 'var(--accent-800)',
  accent900: 'var(--accent-900)',

  // Primary (navy)
  primary50: 'var(--primary-50)',
  primary100: 'var(--primary-100)',
  primary200: 'var(--primary-200)',
  primary300: 'var(--primary-300)',
  primary400: 'var(--primary-400)',
  primary500: 'var(--primary-500)',
  primary600: 'var(--primary-600)',
  primary700: 'var(--primary-700)',
  primary800: 'var(--primary-800)',
  primary900: 'var(--primary-900)',

  // Neutral
  neutral100: 'var(--neutral-100)',
  neutral200: 'var(--neutral-200)',
  neutral300: 'var(--neutral-300)',
  neutral400: 'var(--neutral-400)',
  neutral500: 'var(--neutral-500)',
  neutral600: 'var(--neutral-600)',

  // Semantic
  success: 'var(--success)',
  warning: 'var(--warning)',
  info: 'var(--info)',
  secondary500: 'var(--secondary-500)',
  secondary100: 'var(--secondary-100)',
} as const;

export const fonts = {
  body: 'var(--font-body)',
  mono: 'var(--font-mono)',
} as const;

export const radii = {
  sm: 'var(--radius-sm)',
  md: 'var(--radius-md)',
  lg: 'var(--radius-lg)',
  xl: 'var(--radius-xl)',
  '2xl': 'var(--radius-2xl)',
  full: 'var(--radius-full)',
} as const;
