import type { CSSProperties, SVGProps } from 'react'

interface LocaleFlagProps extends Omit<SVGProps<SVGSVGElement>, 'aria-hidden'> {
  code: string
}

const flagStyle: CSSProperties = {
  borderRadius: 2,
  boxShadow: '0 0 0 1px rgba(0, 0, 0, 0.16)',
  flexShrink: 0,
  height: 14,
  overflow: 'hidden',
  width: 21,
}

export function LocaleFlag({ code, style, ...props }: LocaleFlagProps) {
  const normalized = code.slice(0, 2).toLowerCase()
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      data-testid={`locale-flag-${normalized}`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 16"
      style={{ ...flagStyle, ...style }}
      {...props}
    >
      <FlagMarkup code={normalized} />
    </svg>
  )
}

function FlagMarkup({ code }: { code: string }) {
  switch (code) {
    case 'fr':
      return (
        <>
          <rect width="8" height="16" fill="#0055A4" />
          <rect x="8" width="8" height="16" fill="#FFFFFF" />
          <rect x="16" width="8" height="16" fill="#EF4135" />
        </>
      )
    case 'de':
      return (
        <>
          <rect width="24" height="5.33" fill="#000000" />
          <rect y="5.33" width="24" height="5.34" fill="#DD0000" />
          <rect y="10.67" width="24" height="5.33" fill="#FFCE00" />
        </>
      )
    case 'nl':
      return (
        <>
          <rect width="8" height="16" fill="#000000" />
          <rect x="8" width="8" height="16" fill="#FAE042" />
          <rect x="16" width="8" height="16" fill="#ED2939" />
        </>
      )
    case 'es':
      return (
        <>
          <rect width="24" height="16" fill="#AA151B" />
          <rect y="4" width="24" height="8" fill="#F1BF00" />
        </>
      )
    default:
      return (
        <>
          <rect width="24" height="16" fill="#012169" />
          <path d="M0 0 L24 16 M24 0 L0 16" stroke="#FFFFFF" strokeWidth="4" />
          <path d="M0 0 L24 16 M24 0 L0 16" stroke="#C8102E" strokeWidth="2" />
          <path d="M12 0 V16 M0 8 H24" stroke="#FFFFFF" strokeWidth="6" />
          <path d="M12 0 V16 M0 8 H24" stroke="#C8102E" strokeWidth="3.5" />
        </>
      )
  }
}
