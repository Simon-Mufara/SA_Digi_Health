import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Security Alerts'
      subtitle='Handle lockout alerts, repeated failures, and policy violations.'
      tag='Incident response'
      backHref='/dashboard/security'
      highlights={[
          'Prioritize repeated failed authentication alerts.',
          'Apply temporary lock and verify identity.',
          'Document remediation actions for each alert.'
      ]}
      checklist={[
          'Review open alerts queue',
          'Contain high-risk access attempts',
          'Close alerts with remediation notes'
      ]}
    />
  );
}
