import { createFileRoute } from '@tanstack/react-router';
import { ContractsPage } from '@/pages/contracts-page'; 
import { RequireAuthBanner } from '@/features/auth';

export const Route = createFileRoute('/contracts')({
  component: RouteComponent, 
});

function RouteComponent() {
  return (
    <RequireAuthBanner>
      <ContractsPage />
    </RequireAuthBanner>
  );
} 