import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Clinician Sessions'
      subtitle='Monitor active, waiting, and completed patient intake sessions.'
      tag='Session control'
      backHref='/dashboard/clinician'
      highlights={[
          'Keep waiting-time visibility for patient flow.',
          'Close completed sessions with complete notes.',
          'Prevent duplicate open sessions per patient.'
      ]}
      checklist={[
          'Review active session count',
          'Close completed intakes',
          'Escalate stalled sessions over threshold'
      ]}
    />
  );
}
