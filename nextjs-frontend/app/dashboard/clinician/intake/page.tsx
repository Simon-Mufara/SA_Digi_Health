import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Clinician Intake'
      subtitle='Run biometric-assisted patient intake with identity confidence checks.'
      tag='Frontline intake'
      backHref='/dashboard/clinician'
      highlights={[
          'Capture a clear face image in adequate lighting.',
          'Collect SA ID and visit reason accurately.',
          'Route identified returning patients to correct queue.'
      ]}
      checklist={[
          'Start camera and verify live preview',
          'Capture or upload face image',
          'Submit intake with mandatory visit reason'
      ]}
    />
  );
}
