
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const MainScreen = () => {

    const navigate = useNavigate();

    const handleButton = (route) => {
        navigate(route);
    }

    return (
        <div className="main-screen">
            <h1 className="main-title">Trading Bot</h1>
            <h1 className="strategy-title">Choose Your Strategy</h1>
            <button 
                onClick={() => handleButton('/moving-averages')} 
                className="strategy-button"> 
                Moving Averages 
            </button>
            <button 
                onClick={() => handleButton('/rsi-trading')} 
                className="strategy-button"> 
                RSI
            </button>
            <button
                onClick={() => handleButton('/MACD-trading')}
                className="strategy-button">
                MACD Divergence
            </button>
        </div>
    );
};

export default MainScreen;
