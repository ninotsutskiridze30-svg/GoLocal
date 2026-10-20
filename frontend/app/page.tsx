"use client";

import { useCallback, useMemo, useState } from "react";
import { Discover } from "@/components/Discover";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { Navbar } from "@/components/Navbar";
import { useEventEngine } from "@/hooks/useEventEngine";
import { demoEvents } from "@/lib/demo-events";
import { DEFAULT_FILTERS, applyFilters, type FilterState } from "@/lib/filters";
import { useSavedEvents } from "@/lib/saved";

export default function Home() {
  const { events, status, loading, message, search, restoreEvents } = useEventEngine(demoEvents);
  const { ids: savedIds, toggle } = useSavedEvents();
  const [activeQuery, setActiveQuery] = useState("");
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);

  const searchActive = activeQuery !== "";
  const visible = useMemo(() => applyFilters(events, filters, searchActive), [events, filters, searchActive]);

  const handleSearch = useCallback(async (text: string) => {
    const trimmed = text.trim();
    setActiveQuery(trimmed);
    if (!trimmed) {
      await restoreEvents();
      return;
    }
    await search(trimmed);
  }, [restoreEvents, search]);

  const reset = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    if (activeQuery) void handleSearch("");
  }, [activeQuery, handleSearch]);

  return <>
    <Navbar />
    <main className="flex-1">
      <Hero
        activeQuery={activeQuery}
        loading={loading}
        status={status}
        message={message}
        resultCount={visible.length}
        onSearch={handleSearch}
      />
      <Discover
        filters={filters}
        onFiltersChange={setFilters}
        events={visible}
        totalCount={events.length}
        searchActive={searchActive}
        savedIds={savedIds}
        onToggleSave={toggle}
        onReset={reset}
      />
    </main>
    <Footer />
  </>;
}
