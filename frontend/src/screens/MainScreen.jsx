import './MainScreen.css';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';


const MainScreen = () => {

    const navigate = useNavigate();

    const handleButton = async () => {
        navigate('/moving-averages');
    }

    
    return (
        <div className="main-screen">
            <h1 className="main-title">Trading Bot</h1>
            <h1 className="strategy-title">Choose Your Strategy</h1>
            <button onClick = {handleButton} className = "strategy-button"> 
                Moving Averages 
            </button>
        </div>
    );
};

export default MainScreen;