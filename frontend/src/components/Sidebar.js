import React, {useState, useEffect} from 'react';
import {Home, Search, ClipboardList, BarChart3, Info} from 'lucide-react';
import {checkHealth} from '../services/api.js';

const navItems =[
    {id: 'dashboard', label:'Dashboard', icon: <Home/> },
    {id: 'predict', label:'New Prediction', icon: <Search/> },
    {id:'history', label:'History', icon:<ClipboardList/>},
    {id:'insights', label: 'Model Insights', icon:<BarChart3/>},
    {id:'about', label:'About', icon:<Info/>}
];

export default function Sidebar({activePage, setActivePage}){
    const [apiStatus, setApiStatus] = useState('checking');

    useEffect(()=>{
        checkHealth()
            .then(()=> setApiStatus('connected'))
            .catch(()=> setApiStatus('offine'));

            const interval = setInterval(()=> {
                checkHealth()
                    .then(()=> setApiStatus('connected'))
                    .catch(()=> setApiStatus('offline'));
            }, 30000);
            return () => clearInterval(interval)
    }, []);

    return(
        <div style={styles.sidebar}>
            {/*Logo*/}
            <div style={styles.logo}>
                <span style={styles.logoicon}>ANYX</span>
                <div>
                    <div style={styles.logoTitle}>Livestock Alert</div>
                    <div style={styles.logoSub}>Disease Prediction System</div>
                </div>
            </div>
            {/*Navigation links*/}
            <nav style={styles.nav}>
                {navItems.map((item)=> (
                    <button
                        key={item.id}
                        onClick={()=> setActivePage(item.id)}
                        style={{
                            ...styles.navItem,
                            ...(activePage === item.id ? styles.navItemActive : {})
                        }}>
                            <span style={styles.navIcon}>{item.icon}</span>
                            <span>{item.label}</span>
                        </button>
                ))}
            </nav>
            {/*API status indicator*/}
            <div style={styles.statusBar}>
                <span style={{
                    ...styles.statusDot,
                    backgroundColor: apiStatus === 'connected' ? '##52B788' : '#Dc2626'
                }}/>
                <span style={styles.statusText}>
                    API: {apiStatus === 'connected' ? 'Connected' :
                          apiStatus === 'offline' ? 'Offline': 'Checking...'}
                </span>
            </div>
        </div>
    );
}

const styles ={
    sidebar: {
        width: '220px',
        minHeight : '100vh',
        backgroundColor :'#1b4332',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom:0
    },
    logo: {
        display: 'flex',
        alignItems: 'center',
        gap: '10px', 
        padding: '24px 16px',
        borderBottom: '1px solid #2d6af'
    },
    logoIcon : {fontSize: '28px'},
    logoTitle: {
        coloe: 'white',
        fontWeight: '700',
        fontSize: '15px'
    },
    logoSub: {
        color: '#a8d8a8',
        fontSize: '10px',
        marginTop : '2px'
    },
    nav :{
        flex : '1',
        padding: '16px 0'
    },
    navItem: {
        width: '100%',
        display: 'flex',
        alignItems:'center',
        gap: '12px',
        bacckground:'none',
        vorder:'none',
        color:'#a8d8a8',
        fontSize: '14px',
        cursor: 'pointer',
        textAlign:'left',
        transition:'background 0.2s',
        borderLeft: '3px solid transparent'
    },
    navItemActive: {
        backgroundColor:'#2d6a4f',
        color:'white',
        borderLeft: '3px solid #52B788'  
    },
    navIcon:{
        fontSize:'16px'
    },
    statusBar: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '16px 20px',
        borderTop: '1px solid #2d6a4f'

    },
    statusText:{
        color: '#a8d8a8',
        fontSize:'12px'
    },
    statusDot:{
        width: '8px',
        height:'8px',
        borderRadius: '50%'
    }

};
