import { createFileRoute } from '@tanstack/react-router';
import { ProxyVisualisationPage } from '@/pages/proxy-visualisation-page';
export const Route = createFileRoute('/proxy-visualisation/$visualisationId')({
  component: RouteComponent,
});

function RouteComponent() {
  const { visualisationId } = Route.useParams();
  return <ProxyVisualisationPage id={visualisationId} />;
}