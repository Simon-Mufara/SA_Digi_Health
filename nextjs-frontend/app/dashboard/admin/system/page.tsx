import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Admin System'
      subtitle='Track service health, uptime, and infrastructure readiness.'
      tag='Platform health'
      backHref='/dashboard/admin'
      highlights={[
          'Monitor backend, biometric, and data services.',
          'Respond to degraded status before clinic peak hours.',
          'Maintain incident runbook visibility.'
      ]}
      checklist={[
          'Validate backend and frontend health',
          'Check biometric service status',
          'Log and acknowledge active incidents'
      ]}
    />
  );
}
