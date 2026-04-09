import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Admin Roles'
      subtitle='Approve role changes with least-privilege security controls.'
      tag='RBAC'
      backHref='/dashboard/admin'
      highlights={[
          'Apply minimum required access for each user.',
          'Require reason and approver for elevated roles.',
          'Monitor role mismatch incidents daily.'
      ]}
      checklist={[
          'Review pending role requests',
          'Approve/reject with comments',
          'Publish updated role matrix'
      ]}
    />
  );
}
