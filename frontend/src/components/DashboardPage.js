import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, LineChart, Line, ResponsiveContainer
} from 'recharts';
import { getPredictionStats, getPredictionHistory } from '../services/api.js';

export default function DashboardPage() {
  const [stats, setStats]     = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getPredictionStats(), getPredictionHistory(10)])
      .then(([s, h]) => { setStats(s); setHistory(h); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={styles.loading}>Loading dashboard...</div>;

  const summaryCards = [
    { label: 'Total Predictions', value: stats?.total_predictions ?? 0,   color: '#1B4332' },
    { label: 'High Risk Alerts',  value: stats?.high_risk_count   ?? 0,   color: '#DC2626' },
    { label: 'Low Risk',          value: stats?.low_risk_count    ?? 0,   color: '#16A34A' },
    { label: 'High Risk Rate',    value: stats ? `${(stats.high_risk_rate * 100).toFixed(1)}%` : '0%', color: '#D97706' }
  ];

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>Dashboard</h1>
      <p style={styles.sub}>Overview of all predictions made through the system</p>

      {/* Summary cards */}
      <div style={styles.cardRow}>
        {summaryCards.map(card => (
          <div key={card.label} style={{ ...styles.card, borderTop: `4px solid ${card.color}` }}>
            <div style={{ ...styles.cardValue, color: card.color }}>{card.value}</div>
            <div style={styles.cardLabel}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Recent predictions table */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Recent Predictions</h2>
        <table style={styles.table}>
          <thead>
            <tr>
              {['Time', 'Source', 'Risk Level', 'Probability'].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '20px', color: '#6B7280' }}>
                  No predictions yet. Go to New Prediction to get started.
                </td>
              </tr>
            ) : (
              history.map(row => (
                <tr key={row.id} style={styles.tr}>
                  <td style={styles.td}>
                    {new Date(row.timestamp).toLocaleString()}
                  </td>
                  <td style={styles.td}>
                    <span className={row.source_interface === 'react' ? 'badge-react' : 'badge-ussd'}>
                      {row.source_interface === 'react' ? 'Web' : 'USSD'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span className={row.risk_level === 'HIGH' ? 'badge-high' : 'badge-low'}>
                      {row.risk_level}
                    </span>
                  </td>
                  <td style={styles.td}>
                    {(row.outbreak_probability * 100).toFixed(1)}%
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles = {
  page:         { padding: '32px' },
  loading:      { padding: '32px', color: '#6B7280' },
  heading:      { fontSize: '24px', fontWeight: '700', color: '#1B4332' },
  sub:          { color: '#6B7280', marginTop: '4px', marginBottom: '28px' },
  cardRow:      { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' },
  card:         { background: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  cardValue:    { fontSize: '32px', fontWeight: '700' },
  cardLabel:    { color: '#6B7280', fontSize: '13px', marginTop: '4px' },
  section:      { background: 'white', borderRadius: '8px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  sectionTitle: { fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1B4332' },
  table:        { width: '100%', borderCollapse: 'collapse' },
  th:           { textAlign: 'left', padding: '10px 12px', borderBottom: '2px solid #E5E7EB', fontSize: '12px', color: '#6B7280', textTransform: 'uppercase' },
  tr:           { borderBottom: '1px solid #F3F4F6' },
  td:           { padding: '12px', fontSize: '14px' }
};