import './MovingAverages.css';
import React, { useState, Component } from 'react';
import axios from 'axios';



const MovingAverages = () => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [errorMessage, setErrorMessage] = useState ('');
    const [myStocks, setMyStocks] = useState ([]);
    const [stockInput, setStockInput] = useState('');

    const handleStartDateChange = (e) => {
        setStartDate(e.target.value);
    };

    const handleEndDateChange = (e) => {
        setEndDate(e.target.value);
    };

    const makeSureValidDate = () => {
        if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
            setErrorMessage('Please choose valid dates: the date cannot start after the end date');
        } else {
            setErrorMessage('');
        }
    };

     const handleStockInputChange = (e) => {
        setStockInput(e.target.value);
     }

     const addStock = () => {
        if (stockInput.trim() !== '') {
            setMyStocks([...myStocks, stockInput.trim()]);
            setStockInput('');
        }
     }

     const deleteStock = (index) => {
        const updatedStocks = myStocks.filter((_, i) => i !== index);
        setMyStocks(updatedStocks);
    };

    return (
        <div>
            <h1 className="page-title">Moving Averages Strategy</h1>
            <p className="caption">Please choose the dates you want to test with</p>
            <div className="date-inputs">
                <label htmlFor="start-date">Start Date: </label>
                <input 
                    type="date" 
                    id="start-date" 
                    name="startDate" 
                    value={startDate} 
                    onChange={(e) => {
                        handleStartDateChange(e);
                        makeSureValidDate();
                    }}
                />
                
                <label htmlFor="end-date">End Date: </label>
                <input 
                    type="date" 
                    id="end-date" 
                    name="endDate" 
                    value={endDate} 
                    onChange={(e) => {
                        handleEndDateChange(e);
                        makeSureValidDate();
                    }} 
                />
            </div>
            <p className ="stocks-caption"> Please choose which stocks you would like to trade with</p>
            {errorMessage && (
                <p className="error-message">{errorMessage}</p>  
            )}
            <div className="stock-input-container">
                <input 
                    type="text" 
                    value={stockInput} 
                    onChange={handleStockInputChange} 
                    placeholder="Enter stock symbol"
                    className="stock-input"
                />
                <button onClick={addStock} className="add-stock-button">Add Stock</button>
            </div>

            <ul className="stock-list">
                {myStocks.map((stock, index) => (
                    <li key={index} className="stock-item">
                        {stock}
                        <button className="delete-button" onClick={() => deleteStock(index)}>X</button>
                    </li>
                ))}
            </ul>
        </div>
        
    );
};

export default MovingAverages;