import { createFileRoute } from "@tanstack/react-router";
import { VisualisationPage } from "@/pages/visualisation-page";

export const Route = createFileRoute("/visualisation")({
  component: RouteComponent,
});

function RouteComponent() {
  return <VisualisationPage />;
}