// Deliberately NOT a client component. Rendered by the root layout (a
// Server Component), this script is part of the initial SSR HTML and runs
// before first paint — setting the "dark" class before React even hydrates,
// so there's no flash of the wrong theme. A client component doing the same
// thing would trigger React's "script tag rendered by a component" warning.
const SCRIPT = `(function(){try{var t=localStorage.getItem('theme')||'system';var d=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);}catch(e){}})();`;

export function ThemeInitScript() {
  return <script dangerouslySetInnerHTML={{ __html: SCRIPT }} />;
}
