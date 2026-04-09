import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Doctor Patients'
      subtitle='Track waiting queue, triage priority, and continuity of care handoff.'
      tag='Clinical flow'
      backHref='/dashboard/doctor'
      highlights={[
          'Prioritize high-risk chronic disease patients first.',
          'Review previous diagnoses and medication adherence.',
          'Confirm biometric identity before issuing treatment plans.'
      ]}
      checklist={[
          'Review waiting list and flag urgent cases',
          'Open latest visit timeline and vitals',
          'Document diagnosis and next follow-up date'
      ]}
    />
  );
}
