import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Doctor Schedule'
      subtitle='Manage consultation slots, rooms, and specialist escalation windows.'
      tag='Care operations'
      backHref='/dashboard/doctor'
      highlights={[
          'Balance acute walk-ins with booked follow-ups.',
          'Reserve slots for maternal and NCD monitoring.',
          'Escalate critical findings to referral facilities quickly.'
      ]}
      checklist={[
          'Confirm first 3 patient appointments',
          'Check room allocation and nurse support',
          'Lock emergency escalation slot availability'
      ]}
    />
  );
}
