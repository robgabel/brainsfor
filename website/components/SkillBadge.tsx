export function SkillBadge({ label, mono }: { label: string; mono?: boolean }) {
  return (
    <span
      className={`inline-block rounded-full bg-indigo-mist px-2.5 py-0.5 text-xs font-semibold tracking-wide text-indigo-deep ${
        mono ? "font-mono" : ""
      }`}
    >
      {label}
    </span>
  );
}
