import React, { useState, useEffect } from 'react';
import { getPredictionHistory } from '../services/api';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [filter, setFilter]   = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPredictionHistory(100)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = history.filter(row => {
    if (filter === 'high') return row.risk_level === 'HIGH';
    if (filter === 'low')  return row.risk_level === 'LOW';
    if (filter === 'ussd') return row.source_interface === 'ussd';
    if (filter === 'react') return row.source_interface === 'react';
    return true;
  });

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>Prediction History</h1>
      <p style={styles.sub}>All predictions made through the web dashboard and USSD interface</p>

      {/* Filter buttons */}
      <div style={styles.filters}>
        {[
          { id: 'all',   label: 'All'         },
          { id: 'high',  label: 'High Risk'   },
          { id: 'low',   label: 'Low Risk'    },
          { id: 'react', label: 'Web Only'    },
          { id: 'ussd',  label: 'USSD Only'   }
        ].map(f => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            style={{
              ...styles.filterBtn,
              ...(filter === f.id ? styles.filterActive : {})
            }}
          >
            {f.label}
          </button>
        ))}
        <span style={styles.count}>
          Showing {filtered.length} records
        </span>
      </div>

      {loading ? (
        <div style={{ color: '#6B7280', padding: '20px' }}>Loading...</div>
      ) : (
        <div style={styles.tableWrap}>
          <table style={styles.table}>
            <thead>
              <tr>
                {['ID', 'Timestamp', 'Source', 'Risk Level', 'Probability'].map(h => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: '#9CA3AF' }}>
                    No predictions found for this filter.
                  </td>
                </tr>
              ) : (
                filtered.map(row => (
                  <tr key={row.id} style={styles.tr}>
                    <td style={styles.td}>#{row.id}</td>
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
                        {row.risk_level ?? 'N/A'}
                      </span>
                    </td>
                    <td style={styles.td}>
                      {row.outbreak_probability
                        ? `${(row.outbreak_probability * 100).toFixed(1)}%`
                        : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const styles={
    page:{padding:'32px'},
    heading:{fontSize:'24px', fontweight:'700', color:'#1b4332'},
    sub:{color:'#6b7280', marginTop:'4px', marginBottom:'24px'},
    filters:{display:'flex', gap:'8px', alignItems:'center', marginBottom:'20px', flexWrap:'wrap'},
    filterBtn:{padding:'6px 16px', border:'1px solid #d1d5db', borderRadius:'20px', background:'white', cursor:'pointer', fontSize:'13px', color:'#374151'},
    filterActive:{backgroundColor:'#1b4332', color:'white', bordercolor:'#1b4332'},
    count:{marginLeft:'auto', fontSize:'13px', color:'#6b7280'},
    tableWrap:{background:'white', borderRadius:'8px', padding:'0', boxShadow:'0 1px 3px rgba(0,0,0,0.1)', overflow:'hidden'},
    table:{width:'100%', borderCollapse:'collapse'},
    th:{textAlign:'left', padding:'12px 16px', borderBottom:'2px solid #e5e7eb', fontSize:'12px', color:'#6b7280', textTransform:'uppercase', backgroundColor:'#f9afb'},
    tr:{borderBottom:'1px solid #f3f4f6'},
    td:{pading:'12px 16px', fontSize:'14px'}
}