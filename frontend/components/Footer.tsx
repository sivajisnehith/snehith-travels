export default function Footer() {
  return (
    <footer className="w-full border-t border-zinc-200 bg-zinc-50 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-zinc-500 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p>
          &copy; {new Date().getFullYear()} <strong>Snehith Travels</strong>. Travel booking backend & MVP.
        </p>
        <p className="text-xs text-zinc-400">
          Source of Truth for Saarthi AI Travel Agent integration.
        </p>
      </div>
    </footer>
  );
}
