import { Logo } from "@/components/Logo";

export function Footer() {
  return <footer className="relative mt-10 border-t border-line">
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-12 md:flex-row md:items-center md:justify-between">
      <div className="space-y-3">
        <Logo />
        <p className="max-w-sm text-sm text-muted">Event facts come from the database. The AI only ranks and explains them.</p>
      </div>
      <div className="text-sm text-muted md:text-right">
        <p>Demo listings are fictional and link to no real tickets.</p>
        <p className="mt-1">Photos are generic stock images matched to each event type.</p>
      </div>
    </div>
  </footer>;
}
