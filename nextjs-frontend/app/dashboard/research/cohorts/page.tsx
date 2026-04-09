import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Research Cohorts'
      subtitle='Explore de-identified patient cohorts across SA healthcare patterns.'
      tag='Population insights'
      backHref='/dashboard/research'
      highlights={[
          'Use de-identified data only for analysis.',
          'Track disease burden by age and region.',
          'Support policy planning with evidence-based trends.'
      ]}
      checklist={[
          'Set cohort filters',
          'Review age/gender diagnosis segments',
          'Save cohort snapshot for report'
      ]}
    />
  );
}
