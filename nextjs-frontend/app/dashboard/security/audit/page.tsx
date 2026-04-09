import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Security Audit Log'
      subtitle='Review historical auth and role-access events for compliance.'
      tag='Audit trail'
      backHref='/dashboard/security'
      highlights={[
          'Keep immutable audit trail coverage.',
          'Support incident investigations with exact timelines.',
          'Export filtered logs for governance reviews.'
      ]}
      checklist={[
          'Filter by role and time range',
          'Inspect failed and mismatch events',
          'Export signed audit report'
      ]}
    />
  );
}
