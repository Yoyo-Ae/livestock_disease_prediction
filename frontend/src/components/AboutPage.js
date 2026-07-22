import React from 'react';

const DATA_SOURCES = [
  { name: 'FAO EMPRES-i', desc: 'Global animal disease outbreak records', url: 'https://empres-i.apps.fao.org/' },
  { name: 'FAOSTAT',      desc: 'Livestock population statistics',        url: 'https://www.fao.org/faostat/' },
  { name: 'NASA POWER',   desc: 'Monthly climate data (temperature, rainfall)', url: 'https://power.larc.nasa.gov/' },
  { name: 'WOAH WAHIS',   desc: 'World animal health information system', url: 'https://wahis.woah.org/' }
];

const STEPS = [
  'Go to New Prediction in the left menu',
  'Select your country and disease type',
  'Choose the animal species of concern',
  'Enter the month, year, and season',
  'Enter livestock density and climate values for your area',
  'Enter the number of outbreaks in this area in the past 12 months',
  'Click Run Prediction',
  'Read the risk level and follow the recommended action'
];

export default function AboutPage() {
  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>About This System</h1>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>What This System Does</h2>
        <p style={styles.para}>
          This system predicts the likelihood of livestock disease outbreaks in
          sub-Saharan Africa using machine learning trained on secondary
          epidemiological, climate, and livestock population data. It covers five
          priority transboundary animal diseases — Foot and Mouth Disease,
          Peste des Petits Ruminants, Lumpy Skin Disease, Contagious Bovine
          Pleuropneumonia, and Rift Valley Fever.
        </p>
        <p style={styles.para}>
          Predictions are delivered through two interfaces: this web dashboard
          for veterinary officers and researchers, and a USSD mobile service
          for Nigerian smallholder farmers accessible from any phone without
          internet access. Both interfaces use the same Random Forest prediction
          model trained on data spanning 2005 to 2024.
        </p>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Data Sources</h2>
        <div style={styles.sourceGrid}>
          {DATA_SOURCES.map(src => (
            <div key={src.name} style={styles.sourceCard}>
              <div style={styles.sourceName}>{src.name}</div>
              <div style={styles.sourceDesc}>{src.desc}</div>
              <a href={src.url} target="_blank" rel="noreferrer" style={styles.sourceLink}>
                Visit →
              </a>
            </div>
          ))}
        </div>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>How to Use</h2>
        <ol style={styles.stepList}>
          {STEPS.map((step, i) => (
            <li key={i} style={styles.step}>
              <span style={styles.stepNum}>{i + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <div style={styles.footer}>
        Built by <strong>Uyoyou Annabel Evivie</strong> — Miva Open University, Abuja, Nigeria — 2026
        <br />
        B.Sc. Software Engineering — Final Year Project
        <br /><br />
        Data: FAO EMPRES-i · FAOSTAT · NASA POWER · WOAH WAHIS
      </div>
    </div>
  );
}


const styles = {
  page:        { padding: '32px', maxWidth: '800px' },
  heading:     { fontSize: '24px', fontWeight: '700', color: '#1B4332', marginBottom: '28px' },
  section:     { background: 'white', borderRadius: '8px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px' },
  sectionTitle:{ fontSize: '16px', fontWeight: '600', color: '#1B4332', marginBottom: '16px' },
  para:        { fontSize: '14px', color: '#374151', lineHeight: '1.7', marginBottom: '12px' },
  sourceGrid:  { display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: '12px' },
  sourceCard:  { border: '1px solid #E5E7EB', borderRadius: '8px', padding: '16px' },
  sourceName:  { fontWeight: '600', color: '#1B4332', marginBottom: '4px' },
  sourceDesc:  { fontSize: '13px', color: '#6B7280', marginBottom: '10px' },
  sourceLink:  { fontSize: '13px', color: '#2D6A4F', textDecoration: 'none', fontWeight: '500' },
  stepList:    { listStyle: 'none', padding: 0 },
  step:        { display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '12px', fontSize: '14px', color: '#374151' },
  stepNum:     { minWidth: '26px', height: '26px', backgroundColor: '#1B4332', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: '700' },
  footer:      { textAlign: 'center', padding: '24px', color: '#9CA3AF', fontSize: '13px', lineHeight: '1.8' }
};