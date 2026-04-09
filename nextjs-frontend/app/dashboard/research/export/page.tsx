import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Research Export'
      subtitle='Export secure de-identified datasets for approved analysis workflows.'
      tag='Data governance'
      backHref='/dashboard/research'
      highlights={[
          'Enforce de-identification before export.',
          'Track who exported what and when.',
          'Provide reproducible CSV/JSON outputs.'
      ]}
      checklist={[
          'Select export format and cohort',
          'Validate PII-safe export preview',
          'Download and archive export manifest'
      ]}
    />
  );
}
