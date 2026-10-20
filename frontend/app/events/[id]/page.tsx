import { Suspense } from "react";
import { EventDetailView } from "@/components/EventDetailView";

async function EventContent({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <EventDetailView id={Number(id)} />;
}

export default function EventPage({ params }: { params: Promise<{ id: string }> }) {
  return <Suspense fallback={null}>
    <EventContent params={params} />
  </Suspense>;
}
