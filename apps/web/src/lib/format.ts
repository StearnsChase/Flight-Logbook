export function formatHours(value: number): string {
  return `${value.toFixed(1)} hr`;
}

export function formatDateLabel(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
}
