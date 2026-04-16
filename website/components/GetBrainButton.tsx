export function GetBrainButton({ brainSlug }: { brainSlug: string }) {
  return (
    <a
      href={`/brains/${brainSlug}/${brainSlug}-brain-pack.zip`}
      download
      className="block w-full rounded-lg bg-brain-indigo py-3 text-center text-[15px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98]"
    >
      Get this brain — free
    </a>
  );
}
