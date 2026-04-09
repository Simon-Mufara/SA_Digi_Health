import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Doctor AI Summaries'
      subtitle='Review AI-generated encounter summaries for faster decision-making.'
      tag='AI assist'
      backHref='/dashboard/doctor'
      highlights={[
          'Use summaries as support, not replacement for clinical judgment.',
          'Validate AI flags against patient vitals and history.',
          'Capture final clinician decisions for traceability.'
      ]}
      checklist={[
          'Open summary for each active consultation',
          'Validate risk flags before treatment',
          'Store final signed clinical note'
      ]}
    />
  );
}
