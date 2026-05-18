export default function PageHeader({ eyebrow, title, children }) {
  return (
    <header className="border-b border-ink/10 bg-white px-5 py-5 sm:px-8">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
        {eyebrow}
      </p>
      <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <h1 className="text-2xl font-semibold tracking-normal sm:text-3xl">
          {title}
        </h1>
        {children ? <div className="flex flex-wrap gap-2">{children}</div> : null}
      </div>
    </header>
  );
}
