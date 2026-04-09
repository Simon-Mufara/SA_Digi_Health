import RoleSectionPage from '@/components/RoleSectionPage';

export default function Page() {
  return (
    <RoleSectionPage
      title='Security Live Feed'
      subtitle='Observe real-time authentication events and access anomalies.'
      tag='Live security'
      backHref='/dashboard/security'
      highlights={[
          'Watch failed login spikes per staff ID.',
          'Correlate unusual IPs with role attempts.',
          'Escalate suspicious behavior in real time.'
      ]}
      checklist={[
          'Monitor live event stream',
          'Validate top failed-auth source',
          'Trigger alert escalation when threshold breached'
      ]}
    />
  );
}
