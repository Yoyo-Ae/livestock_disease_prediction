import React, {useState, useEffect} from 'react';
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

export default function PredictionPage(){
    const [form,setForm] = useState(intailForm);
    const [result, setResult] = useState(null);
    const [loading, setLoading] =useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const {name, value} = e.target;
        setForm(prev => ({
            ...prev,
            [name]: ['year', 'month', 'livestock_density','rainfall_mm', 'temp_celsuis', 
                'rolling_outbreak_count'].includes(name) ? parseFloat(value): value
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
                setError('Prediction failed.Make sure the API is running at 8000.');
        }finally {
                setLoading(false);
        }
    };

    const Field = ({label, name, type = 'select', options, min,max,step}) => (
        <div style={styles.field}>
            <label styles={styles.label}>{label}</label>
            {type === 'select' ? (
                <select name={name} value={form[name]} onChange = {handleChange} style={styles.input}>
                    {options.map(o => (
                        <option key ={o.value ?? o}>
                            {o.label ?? o}
                        </option>
                    ))}
                </select>
            ): type === 'radio'? (
                <div styles={{display: 'flex', gap:'16px', marginTop: '6px' }}>
                    {options.map(o => (
                        <label key={o} style={{display:'flex',alignItems:'center', gap:'6px', fontSize:'14px'}}>
                            <input type="radio" name={name} value={o} checked={form[name] === o} onChange={handleChange}/>{o}
                        </label>
                    ))}</div>
            ): (<input type="number"
                 name={name} 
                 value={form[name]} 
                 onChange={handleChange} 
                 min={min} max={max} 
                 step={step ?? 'any'} 
                 style={styles.input}/>

            )}
        </div>
    );
    return (
        <div style={styles.page}>
            <h1 style={styles.heading}>New Prediction</h1>
            <p style={styles.sub}>Enter the parameters below to predict disease outbreak risk</p>

            <div style={styles.layout}>
                {/*fORM*/}
                <div style={styles.formCard}>
                    <h2 style ={styles.sectionTitle}>Input Parameters</h2>

                    <Field label="Country" name="country" options={COUNTRIES}/>
                    <Field label ="Disease Type" name="disease_type" options={DISEASES}/>
                    <Field label="Species" name="species" options={SPECIES}/>
                    <Field label="Month" name="month" options={MONTHS}/>
                    <Field label="Year" name="year" type="number" min={2005} max={2030}/>
                    <Field label="Season" name="season" type="radio" options={['Wet', 'Dry']}/>
                    <Field label="Livestock Density (animal/km2)" name="livestock_density" type="number" min={0} step={0.1}/>
                    <Field label="Rainfall (mm)" name="rainfall_mm" type="number" min={0} step={0.1}/>
                    <Field label="Temperature" name="temp_celsuis" type="number" step={0.1}/>
                    <Field label="Outbreak in past 12 months" name="rolling_outbreak_count" type="number" min={0} max={50}/>

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
                            {/*RISK BANNER*/}
                            <div style={{...styles.riskBanner, backgroundColor: result.risk_level === 'HIGH' ? '#dc2626': '#16a34a'}}>
                                {result.risk_level === 'HIGH' ? (<><TriangleAlert/>HIGH RISK</>): (<><CircleCheck/>LOW RISK</>)}
                            </div>
                            {/*PROBABILITY*/}
                            <div styles={styles.probSection}>
                                <div styles={styles.probValue}>
                                    {(result.outbreak_probability * 100).toFixed(1)}%
                                </div>
                                <div style={styles.probLabel}>Outbreak Probability</div>
                            </div>
                            {/*PROBABILITY BAR*/}
                            <div style={styles.barContainer}>
                                <div style={styles.barTrack}>
                                    <div style={{...styles.barFill, width:`${result.outbreak_probability * 100}%`, backgroundColor:result.risk_level === 'HIGH'? '#dc2626': '#16a36a'}}/>
                                {/*THRESHOLD MARKER*/}
                                <div style={{...styles.thresholdMarker, left: `${result.threshold_used * 100}%`}}/>
                                </div>
                                <div style={styles.barLabels}>
                                    <span>0%</span>
                                    <span style={{color: '#d97706', fontSize:'11px'}}>
                                        <TriangleAlert/> Threshold ({(result.threshold_used *100).toFixed(0)}%)
                                    </span>
                                    <span>100%</span>
                                </div>
                            </div>
                            {/*MESSAGE*/}
                            <div style={styles.message}>{result.message}</div>
                            {/*INPUT SUMMARY*/}
                            <div style={styles.inputSummary}>
                                <div style={styles.summaryTitle}>Inputs Used</div>
                                {[
                                    ['Country', form.country],
                                    ['Disease', form.disease_type],
                                    ['Species', form.species],
                                    ['Period', `${MONTHS.find(m=>m.value===form.month)?.label} ${form.year}`],
                                    ['Season', form.season],
                                    ['Model', result.model_name]
                                ].map(([k,v])=> (
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