import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Admin Staff'
      subtitle='Manage staff accounts, activation status, and compliance records.'
      tag='Governance'
      backHref='/dashboard/admin'
      highlights={[
          'Ensure each staff member has a valid role.',
          'Deactivate dormant accounts quickly.',
          'Audit account changes with timestamp history.'
      ]}
      checklist={[
          'Review active vs inactive users',
          'Check recent account edits',
          'Approve pending staff onboarding'
      ]}
    />
  );
}
