import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getModelInfo, getFeatureImportance } from '../services/api';

const MODELS = [
  { name: 'Logistic Regression', accuracy: 0.9321, precision: 0.2252, recall: 0.7363, f1: 0.3449, auc: 0.8921, best: false },
  { name: 'Random Forest',       accuracy: 0.9812, precision: 0.6258, recall: 0.5604, f1: 0.5913, auc: 0.9303, best: true  },
  { name: 'XGBoost',             accuracy: 0.9779, precision: 0.5460, recall: 0.5220, f1: 0.5337, auc: 0.8363, best: false }
];

export default function InsightsPage() {
  const [meta, setMeta]       = useState(null);
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getModelInfo(), getFeatureImportance()])
      .then(([m, f]) => { setMeta(m); setFeatures(f); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: '32px', color: '#6B7280' }}>Loading model data...</div>;

  const chartData = features
    .slice(0, 10)
    .map(f => ({
      name: f.feature.replace(/_/g, ' '),
      importance: parseFloat((f.mean_abs_shap ?? f.importance ?? 0).toFixed(4))
    }))
    .sort((a, b) => b.importance - a.importance);

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>Model Insights</h1>
      <p style={styles.sub}>Performance metrics, feature importance, and model selection rationale</p>

      {/* Info cards */}
      <div style={styles.cardRow}>
        {[
          { label: 'Model Type',    value: 'Random Forest'                                },
          { label: 'AUC-ROC',       value: meta?.auc_roc?.toFixed(4)  ?? '0.9303'        },
          { label: 'F1-Score',      value: meta?.f1_score?.toFixed(4)  ?? '0.5913'        },
          { label: 'Threshold',     value: meta?.optimal_threshold ?? '0.30'              }
        ].map(c => (
          <div key={c.label} style={styles.card}>
            <div style={styles.cardVal}>{c.value}</div>
            <div style={styles.cardLabel}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* Feature importance chart */}
      {chartData.length > 0 && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Feature Importance (SHAP)</h2>
          <p style={styles.sectionSub}>
            Features ranked by their average contribution to outbreak predictions.
            Rolling outbreak count is the strongest predictor — areas with recent
            outbreak history are significantly more likely to experience new outbreaks.
          </p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ left: 160, right: 20, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={150} />
              <Tooltip formatter={(v) => [v.toFixed(4), 'SHAP Value']} />
              <Bar dataKey="importance" fill="#2D6A4F" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Model comparison table */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Model Comparison</h2>
        <table style={styles.table}>
          <thead>
            <tr>
              {['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC-ROC'].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MODELS.map(m => (
              <tr key={m.name} style={{
                ...styles.tr,
                backgroundColor: m.best ? '#F0FDF4' : 'white'
              }}>
                <td style={styles.td}>
                  {m.name}
                  {m.best && (
                    <span style={styles.bestBadge}>✓ Deployed</span>
                  )}
                </td>
                <td style={styles.td}>{m.accuracy.toFixed(4)}</td>
                <td style={styles.td}>{m.precision.toFixed(4)}</td>
                <td style={styles.td}>{m.recall.toFixed(4)}</td>
                <td style={styles.td}>{m.f1.toFixed(4)}</td>
                <td style={styles.td}>{m.auc.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={styles.note}>
          <strong>Why Random Forest?</strong> Random Forest achieved the highest
          AUC-ROC (0.9303), indicating superior ability to discriminate between
          outbreak and non-outbreak conditions. The decision threshold was set to
          0.30 — lower than the default 0.50 — to prioritise recall over precision,
          reflecting the asymmetric cost of missing an outbreak versus a false alarm
          in livestock disease surveillance.
        </div>
      </div>
    </div>
  );
}

const styles={
    page:{padding:'32px'},
    heading:{fontSize:'24px', fontweight:'700', color:'#1b4332'},
    sub:{color:'#6b7280', marginTop:'4px', marginBottom:'24px'},
    cardRow:{display:'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap:'16px', marginBottom:'24px'},
    card:{background:'white', borderRadius:'8px', padding:'20px', boxShadow:'0 1px 3px rgba(0,0,0,0.1)', borderTop:'4px solid #1b4332'},
    cardVal:{fontSize:'24px', fontWeight:'700', color:'#1b4332'},
    cardLabel:{color:'#6b7280',fontSize:'13px',marginTop:'4px'},
    section:{background:'white', borderRadius:'8px', padding:'24px', boxShadow:'0 1px 3px rgba(0,0,0,0.1)', marginBottom:'24px'},
    sectionTitle:{fontSize:'16px', fontWeight:'600', marginBottom:'8px', color:'#1b4332'},
    sectionSub:{color:'#6b7280', fontSize:'13px', marginBottom:'20px', lineHeight:'1.5'},
    table:{width:'100%',borderCollapse:'collapse'},
    th:{textAlign:'left', padding:'10px 12px', borderBottom:'2px solid #e5e7eb',fontSize:'12px',color:'#6b7280',textTransform:'uppercase'},
    tr:{borderBottom:'1px,solid #f3f4f6'},
    td:{padding:'12px',fontSize:'14px'},
    bestBadge:{marginLeft:'8px', backgroundColor:'#16a34a', color:'white', padding:'2px 8px', borderRadius:'10px', fontSize:'11px', fontWeight:'600'},
    note:{marginTop:'20px', padding:'14px', backgroundColor:'#f0fdf4', borderRadius:'8px', fontSize:'13px', color:'166534', lineHeight:'1.6' ,border:'1px solid #bbf7d0' }
}