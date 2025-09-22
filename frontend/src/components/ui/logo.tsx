interface LogoProps {
  className?: string;
  size?: number;
}

export function Logo({ className = "", size = 32 }: LogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      className={className}
      role="img"
      aria-labelledby="logo-title logo-desc"
    >
      <title id="logo-title">leggen — stylized italic L</title>
      <desc id="logo-desc">
        Square gradient background with italic white L.
      </desc>

      <defs>
        <linearGradient id="logo-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0b74de" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>

      {/* Square background */}
      <rect width="32" height="32" fill="url(#logo-bg)" rx="4" />

      {/* Italic L */}
      <text
        x="11"
        y="22"
        fontFamily="Inter, Roboto, Arial, sans-serif"
        fontWeight="700"
        fontSize="20"
        fontStyle="italic"
        fill="#fff"
      >
        L
      </text>
    </svg>
  );
}
