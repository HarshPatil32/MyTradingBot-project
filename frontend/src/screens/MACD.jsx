import './MovingAverages.css';
import React, { useState, Component } from 'react';
import axios from 'axios';



const MACDTrading = () => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [errorMessage, setErrorMessage] = useState ('');
    const [myStocks, setMyStocks] = useState ([]);
    const [stockInput, setStockInput] = useState('');
    const [results, setResults] = useState('');
    const [initialBalance, setInitialBalance] = useState(100000); 
    const [spyFinalBalance, setSpyFinalBalance] = useState(null);

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
        const trimmedStock = stockInput.trim();
        if (trimmedStock !== '' && !myStocks.includes(trimmedStock.toUpperCase())) {
            setMyStocks([...myStocks, trimmedStock.toUpperCase()]);
            setStockInput('');
            setErrorMessage(''); 
        } else if (myStocks.includes(trimmedStock.toUpperCase())) {
            setErrorMessage('Stock already added.');
        }
    };

     const deleteStock = (index) => {
        const updatedStocks = myStocks.filter((_, i) => i !== index);
        setMyStocks(updatedStocks);
    };

    const handleMACD = async() => {
        if (!startDate || !endDate || myStocks.length === 0) {
            setErrorMessage('Please ensure valid dates and stocks are selected');
            return;
        }

        try {
            const response = await axios.get('http://localhost:5000/MACD-strategy', {
                params: {
                    stocks: myStocks.join(','),
                    start_date: startDate,
                    end_date: endDate,
                    initial_balance: initialBalance
                }
            });
            setResults(response.data);
        } catch (error) {
            console.error('Error fetching MACD data: ', error);
            setErrorMessage('Failed to fetch MACD data');
        }
    }

    const handleSpyInvestment = async () => {
        if (!startDate || !endDate || !initialBalance) {
            setErrorMessage('Please enter valid dates and an initial investment amount.');
            return;
        }

        try {
            const response = await axios.get('http://localhost:5000/spy-investment', {
                params: {
                    start_date: startDate,
                    end_date: endDate,
                    initial_balance: initialBalance
                }
            });
            setSpyFinalBalance(response.data.final_balance);
            setErrorMessage('');
        } catch (error) {
            console.error('Error fetching SPY investment:', error);
            setErrorMessage('Failed to fetch SPY investment data');
        }
    };

    return (
        <div>
            <h1 className="page-title">MACD divergence Strategy</h1>
            <p className="caption">Please choose the dates you want to test with (Please don't
            choose anything before 2016, Alpaca API doesn't have data before then)
            </p>
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

            <h2>SPY Investment Calculator</h2>
            <div className="spy-investment">
                <label>Initial Investment ($):</label>
                <input
                    type="number"
                    value={initialBalance}
                    onChange={(e) => setInitialBalance(e.target.value)}
                />
                <button onClick={handleSpyInvestment} className="fetch-data-button">Calculate SPY Investment</button>
                {spyFinalBalance !== null && (
                    <div className="spy-results">
                        <h3>Investment Results</h3>
                        <p>Initial Investment: ${initialBalance}</p>
                        <p>Final Balance: ${spyFinalBalance.toFixed(2)}</p>
                    </div>
                )}
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

            <button onClick={handleMACD} className="fetch-data-button">Fetch data</button>
            {results && (
                <div className="results">
                    <h2>Backtest Results</h2>
                    <pre 
                        dangerouslySetInnerHTML={{
                            __html: JSON.stringify(results, null, 2).replace(/\n/g, '<br />')
                        }} 
                    />
                </div>
            )}

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

export default MACDTrading;