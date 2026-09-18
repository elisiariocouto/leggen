interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  /** Stroke for the line; the end marker takes `endColor`. */
  color?: string;
  endColor?: string;
  className?: string;
}

/**
 * A bare trend line for table cells and stat tiles: no axes, no labels, the
 * shape is the message and the neighbouring cells carry the numbers.
 */
export default function Sparkline({
  values,
  width = 72,
  height = 20,
  color = "var(--color-muted-foreground)",
  endColor = "var(--color-foreground)",
  className,
}: SparklineProps) {
  if (values.length < 2) return null;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const x = (i: number) => 3 + (i / (values.length - 1)) * (width - 6);
  const y = (v: number) =>
    max === min ? height / 2 : 3 + (1 - (v - min) / (max - min)) * (height - 6);
  const points = values.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  const last = values.length - 1;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className={className}
      aria-hidden="true"
    >
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle cx={x(last)} cy={y(values[last])} r={2.5} fill={endColor} />
    </svg>
  );
}
