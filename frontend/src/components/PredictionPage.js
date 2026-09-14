import React, {useState, useEffect, useCallback} from 'react';
import {runPrediction} from '../services/api.js';
import {COUNTRIES, DISEASES, SPECIES, MONTHS} from '../utils/constants.js';
import {Search, Hourglass, TriangleAlert, CircleCheck} from 'lucide-react'

const intailForm = {
    country: 'Nigeria',
    disease_type: 'Foot and mouth disease',
    species: 'Cattle',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    season :'wet',
    livestock_density: 42.5,
    rainfall_mm: 85.0,
    temp_celsuis: 29.8,
    rolling_outbreak_count: 2

};

function Field ({label, name, type = 'select', options, min,max,step, value, onChange}) {
        return (
        <div style={styles.field}>
            <label styles={styles.label}>{label}</label>
            {type === 'select' ? (
                <select name={name} value={value} onChange = {onChange} style={styles.input}>
                    {options.map(o => (
                        <option key ={o.value ?? o} value={o.value ?? 0}>
                            {o.label ?? o}
                        </option>
                    ))}
                </select>
            ): type === 'radio'? (
                <div styles={{display: 'flex', gap:'16px', marginTop: '6px' }}>
                    {options.map(o => (
                        <label key={o} style={{display:'flex',alignItems:'center', gap:'6px', fontSize:'14px'}}>
                            <input type="radio" name={name} value={o} checked={value === o} onChange={onChange}/>{o}
                        </label>
                    ))}</div>
            ): (<input type="number"
                 name={name} 
                 value={value} 
                 onChange={onChange} 
                 min={min} max={max} 
                 step={step ?? 'any'} 
                 style={styles.input}/>

            )}
        </div>
    );}



export default function PredictionPage(){
    const [form,setForm] = useState(intailForm);
    const [result, setResult] = useState(null);
    const [loading, setLoading] =useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const {name, value} = e.target;
        const numericFields = ['year', 'month', 'livestock_density','rainfall_mm', 'temp_celsuis', 
                'rolling_outbreak_count']
        setForm(prev => ({
            ...prev,
            [name]: numericFields.includes(name) && value !== '' && !isNaN(value) ? Number(value): value
        }));
    };
    
    const handleSubmit = async () => {
        setLoading(true);
        setError(null);
        setResult(null);
        try{
            const data = await runPrediction(form);
            setResult(data);
        }catch (err){
                setError('Prediction failed.Make sure the API is running at 8000 or refill ALL form inputs');
        }finally {
                setLoading(false);
        }
    };
    
    

    const RISK_CONFIG = {
            HIGH:     { bg: '#DC2626', emoji: '⚠',  label: 'HIGH RISK'     },
            MODERATE: { bg: '#D97706', emoji: '⚡', label: 'MODERATE RISK' },
            LOW:      { bg: '#16A34A', emoji: '✓',  label: 'LOW RISK'       }
    };
    return (
        <div style={styles.page}>
            <h1 style={styles.heading}>New Prediction</h1>
            <p style={styles.sub}>Enter the parameters below to predict disease outbreak risk</p>

            <div style={styles.layout}>
                {/*fORM*/}
                <div style={styles.formCard}>
                    <h2 style ={styles.sectionTitle}>Input Parameters</h2>

                    <Field label="Country" name="country" options={COUNTRIES} value={form.country} onChange={handleChange}/>
                    <Field label ="Disease Type" name="disease_type" options={DISEASES} value={form.disease_type} onChange={handleChange}/>
                    <Field label="Species" name="species" options={SPECIES} value={form.species} onChange={handleChange}/>
                    <Field label="Month" name="month" type="select" options={MONTHS} value={form.month} onChange={handleChange}/>
                    <Field label="Year" name="year" type="number" min={2005} max={2030} value={form.year} onChange={handleChange}/>
                    <Field label="Season" name="season" type="radio" options={['Wet', 'Dry']} value={form.season} onChange={handleChange}/>
                    <Field label="Livestock Density (animal/km2)" name="livestock_density" type="number" value={form.livestock_density} onChange={handleChange}/>
                    <Field label="Rainfall (mm)" name="rainfall_mm" type="number" min={0} step={0.1} value={form.rainfall_mm} onChange={handleChange}/>
                    <Field label="Temperature" name="temp_celsuis" type="number" step={0.1} value={form.temp_celsuis} onChange={handleChange}/>
                    <Field label="Outbreak in past 12 months" name="rolling_outbreak_count" type="number" min={0} max={50} value={form.rolling_outbreak_count} onChange={handleChange}/>

                    <button onClick={handleSubmit} disabled={loading} style={{...styles.btn, opacity: loading ? 0.7 : 1}}>
                        {loading ? (<><Hourglass/> Predicting...</>) : (<><Search/> Run Prediction</>)}

                    </button>
                    {error && <div style={styles.error}>{error}</div>}
                </div>

                {/*RESULT*/}
                <div style={styles.resultCard}>
                    <h2 style={styles.sectionTitle}>Result</h2>
                    {!result && !loading &&(
                        <div style={styles.placeholder}>Fill in the form and click Run Prediction to see results.</div>
                    )}
                    {loading && (
                        <div style={styles.placeholder}>Running Prediction...</div>
                    )}
                   

                
                    {result && (
                        <div>
                            {/* Risk banner */}
                            <div style={{
                                ...styles.riskBanner,
                                backgroundColor: RISK_CONFIG[result.risk_level]?.bg || '#6B7280'
                                }}>
                                {RISK_CONFIG[result.risk_level]?.emoji} {RISK_CONFIG[result.risk_level]?.label}
                            </div>

                            {/* Probability */}
                            <div style={styles.probSection}>
                                <div style={styles.probValue}>
                                    {(result.outbreak_probability * 100).toFixed(1)}%
                                </div>
                                <div style={styles.probLabel}>Outbreak Probability</div>
                            </div>

                            {/* Three-zone probability bar */}
                            <div style={styles.barContainer}>
                                <div style={styles.barTrack}>
                                    {/* Low zone */}
                                    <div style={{
                                        position: 'absolute', left: '0%', width: '10%',
                                        height: '100%', backgroundColor: '#DCFCE7',
                                        borderRadius: '6px 0 0 6px'
                                    }}/>
                                    {/* Moderate zone */}
                                    <div style={{
                                        position: 'absolute', left: '10%', width: '10%',
                                        height: '100%', backgroundColor: '#FEF9C3'
                                    }}/>
                                    {/* High zone */}
                                    <div style={{
                                        position: 'absolute', left: '20%', width: '80%',
                                        height: '100%', backgroundColor: '#FEE2E2',
                                        borderRadius: '0 6px 6px 0'
                                    }}/>
                                    {/* Probability marker */}
                                    <div style={{
                                        position: 'absolute',
                                        left: `${result.outbreak_probability * 100}%`,
                                        top: '-6px',
                                        width: '4px',
                                        height: '24px',
                                        backgroundColor: '#1B4332',
                                        transform: 'translateX(-50%)',
                                        borderRadius: '2px',
                                        zIndex: 10
                                    }}/>
                                </div>
                                <div style={styles.barLabels}>
                                    <span style={{ color: '#16A34A' }}>LOW</span>
                                    <span style={{ color: '#D97706', marginLeft: '10%' }}>MODERATE</span>
                                    <span style={{ color: '#DC2626', marginLeft: '10%' }}>HIGH RISK</span>
                                    <span style={{ marginLeft: 'auto' }}>100%</span>
                                </div>
                            </div>

                            {/* Message */}
                            <div style={{
                                ...styles.message,
                                backgroundColor:result.risk_level === 'HIGH'     ? '#FEF2F2' :
                                                result.risk_level === 'MODERATE' ? '#FFFBEB' : '#F0FDF4',
                                borderColor:    result.risk_level === 'HIGH'     ? '#FECACA' :
                                                result.risk_level === 'MODERATE' ? '#FDE68A' : '#BBF7D0',
                                color:          result.risk_level === 'HIGH'     ? '#991B1B' :
                                                result.risk_level === 'MODERATE' ? '#92400E' : '#166534'
                            }}>
                                {result.message}
                            </div>

                            {/* Input summary stays the same */}
                            <div style={styles.inputSummary}>
                                <div style={styles.summaryTitle}>Inputs Used</div>
                                {[
                                    ['Country',  form.country],
                                    ['Disease',  form.disease_type],
                                    ['Species',  form.species],
                                    ['Period',   `${MONTHS.find(m=>m.value===form.month)?.label} ${form.year}`],
                                    ['Season',   form.season],
                                    ['Model',    result.model_name],
                                ].map(([k, v]) => (
                                    <div key={k} style={styles.summaryRow}>
                                        <span style={styles.summaryKey}>{k}</span>
                                        <span style={styles.summaryVal}>{v}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
const styles={
    page: {padding:'32px'},
    heading:{fontSize:'24px', fontWeight:'700', color:'#1b4332'},
    sub: {color:'#6b7280', marginTop: '4px', marginBottom:'28px'},
    layout:{display:'grid', gridTemplateColumn:'1fr 1fr', gap:'24px'},
    formCard:{background:'white', borderRadius:'8px', padding:'24px',boxshadow:'0, 1px 3px rgba(0,0,0,0.1)'},
    resultCard:{background:'white', borderRadius:'8px', padding:'24px',boxshadow:'0, 1px 3px rgba(0,0,0,0.1)'},
    sectionTitle:{fontSize:'16px', fontWeight:'600', marginBottom:'20px', color:'#1b4332',},
    field:{marginBottom:'16px'},
    label:{display:'block', fontSize:'13px', fontWeight:'500', color:'#374151', marginBottom:'6px'},
    input:{width:'100%', padding:'8px 12px', border:'1px solid #d1d5db', borderRadius:'6px', fontSize:'14px', outline:'none'},
    btn:{width:'100%', padding:'12px', backgroundColor:'#1b4332', color:'white', border:'none', borderRadius:'6px', fontSize:'15px', fontWeight:'600', cursor:'pointer', marginTop:'8px'},
    error:{marginTop:'12px', padding:'10px', backgroundColor:'#fef2f', color:'#dc2626', borderRadius:'6px', fontSize:'13px'},
    placeholder:{color:'#9ca3af', textAlign:'center', padding:'48px 24px', fontSize:'14px'},
    riskBanner:{color:'white', fontWeight:'700', fontSize:'20px', padding:'16px', borderRadius:'8px', textAlign:'center', marginBottom:'20px'},
    probSection:{textAlign:'center', marginBottom:'16px'},
    probValue:{fontSize:'48px', fontWeight:'700', color:'#1b4332'},
    probLabel:{color:'#6b7280', fontSize:'13px'},
    barContainer:{marginBottom:'20px'},
    barTrack:{height:'12px', backgroundColor:'#e5e7eb', borderRadius:'6px', position:'relative', overflow:'visible'},
    barFill:{height:'100%', borderRadius:'6px', transition:'width 0.5s ease'},
    thresholdMarker:{position:'absolute', top:'-4px', width:'2px', height:'20px', backgroundColor:'#d97706', transfrom:'translateX(-50%'},
    barLabels:{display:'flex', justifyContent:'space-between', marginTop:'6px', fontSize:'11px', color:'#9ca3af'},
    message:{backgroundColor:'#f0fdf4', border:'1px solid #bbf7d0', borderRadius:'8px', padding:'14px', fontSize:'14px', color:'#166534', marginBottom:'20px', lineHeight:'1.5'},
    inputSummary:{backgroundColor:'#f9fafb', borderRadius:'8px', padding:'14px'},
    summaryTitle:{fontSize:'12px', fontWeight:'600', color:'#6b7280', textTransform:'uppercase', marginBottom:'10px'},
    summaryRow:{display:'flex', justifyContent:'space-between', padding:'4px 0', borderBottom:'1px solid #e5e7eb', fontSize:'13px'},
    summaryKey:{color:'#6b7280'},
    summaryVal:{fontWeight:'500'}

}