import { createFileRoute } from '@tanstack/react-router';
import { ProxyNotificationPage } from '@/pages/proxy-notification-page';

export const Route = createFileRoute('/proxy-notification/$notificationId')({
  component: RouteComponent,
});

function RouteComponent() {
  const { notificationId } = Route.useParams();
  return <ProxyNotificationPage id={notificationId} />;
}