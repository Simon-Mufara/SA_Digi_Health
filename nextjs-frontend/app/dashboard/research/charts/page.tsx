import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Research Charts'
      subtitle='Visualize monthly trends, burden shifts, and treatment outcomes.'
      tag='Visual analytics'
      backHref='/dashboard/research'
      highlights={[
          'Compare seasonal disease variation.',
          'Highlight interventions tied to better outcomes.',
          'Present clear charts for non-technical stakeholders.'
      ]}
      checklist={[
          'Refresh trend data',
          'Annotate critical pattern changes',
          'Export chart image for presentation'
      ]}
    />
  );
}
