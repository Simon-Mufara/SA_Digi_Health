import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Clinician Vitals'
      subtitle='Capture vitals for triage and downstream clinical decision support.'
      tag='Triage'
      backHref='/dashboard/clinician'
      highlights={[
          'Ensure blood pressure and oxygen readings are complete.',
          'Flag abnormal values for immediate review.',
          'Sync vitals with encounter before doctor review.'
      ]}
      checklist={[
          'Record BP, temperature, O2, weight',
          'Mark abnormal findings',
          'Save and attach vitals to active session'
      ]}
    />
  );
}
