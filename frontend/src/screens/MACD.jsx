import React, { useState } from 'react';
import axios from 'axios';
import './MACD.css';

const MACDTrading = () => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [myStocks, setMyStocks] = useState([]);
    const [stockInput, setStockInput] = useState('');
    const [initialBalance, setInitialBalance] = useState(100000);
    const [backtestResult, setBacktestResult] = useState(null);
    const [spyFinalBalance, setSpyFinalBalance] = useState(null);

    const handleStartDateChange = (e) => setStartDate(e.target.value);
    const handleEndDateChange = (e) => setEndDate(e.target.value);
    const handleStockInputChange = (e) => setStockInput(e.target.value);

    const addStock = () => {
        const trimmed = stockInput.trim().toUpperCase();
        if (trimmed && !myStocks.includes(trimmed)) {
            setMyStocks([...myStocks, trimmed]);
            setStockInput('');
            setErrorMessage('');
        } else if (myStocks.includes(trimmed)) {
            setErrorMessage('Stock already added.');
        }
    };

    const deleteStock = (index) => {
        const updatedStocks = myStocks.filter((_, i) => i !== index);
        setMyStocks(updatedStocks);
    };

    const validateInputs = () => {
        if (!startDate || !endDate || new Date(startDate) > new Date(endDate)) {
            setErrorMessage('Please select a valid date range.');
            return false;
        }
        if (!initialBalance || isNaN(initialBalance) || Number(initialBalance) <= 0) {
            setErrorMessage('Please enter a valid initial investment amount.');
            return false;
        }
        return true;
    };

    const runBacktest = async () => {
        if (!validateInputs() || myStocks.length === 0) {
            setErrorMessage('Please ensure valid dates and at least one stock is selected.');
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

            setBacktestResult(response.data);
            setErrorMessage('');
        } catch (error) {
            console.error('Error fetching MACD data:', error);
            setErrorMessage('Failed to fetch MACD data');
        }
    };

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
        <div className="macd-wrapper">
            <div className="macd-card">
                <h1 className="macd-title">📈 MACD Divergence Strategy Simulator</h1>
                <p className="macd-description">
                    Backtest a MACD-based trading strategy using your chosen stocks and compare it against investing the same amount in the SPY ETF.
                </p>

                <div className="macd-section">
                    <h2 className="section-title">1. Select Date Range</h2>
                    <div className="input-row">
                        <label>Start Date:</label>
                        <input type="date" value={startDate} onChange={handleStartDateChange} />
                        <label>End Date:</label>
                        <input type="date" value={endDate} onChange={handleEndDateChange} />
                    </div>
                </div>

                <div className="macd-section">
                    <h2 className="section-title">2. Set Investment Amount</h2>
                    <p className="small-note">This amount will be used for both the MACD strategy and SPY comparison.</p>
                    <input
                        type="number"
                        value={initialBalance}
                        onChange={(e) => setInitialBalance(e.target.value)}
                        placeholder="e.g., 100000"
                    />
                    <button onClick={handleSpyInvestment}>💼 Calculate SPY Investment</button>
                    {spyFinalBalance !== null && (
                        <div className="spy-results">
                            <h3>SPY Investment Results</h3>
                            <p>Initial Investment: ${initialBalance}</p>
                            <p>Final Balance: ${Number(spyFinalBalance).toFixed(2)}</p>
                        </div>
                    )}
                </div>

                <div className="macd-section">
                    <h2 className="section-title">3. Choose Stocks to Trade with MACD</h2>
                    <div className="input-row">
                        <input
                            type="text"
                            value={stockInput}
                            onChange={handleStockInputChange}
                            placeholder="e.g., AAPL"
                        />
                        <button onClick={addStock}>Add Stock</button>
                    </div>
                    <ul className="stock-list">
                        {myStocks.map((stock, idx) => (
                            <li key={idx} className="stock-item">
                                {stock}
                                <button className="delete-button" onClick={() => deleteStock(idx)}>X</button>
                            </li>
                        ))}
                    </ul>
                </div>

                {errorMessage && <div className="error-box">{errorMessage}</div>}

                <div className="macd-footer">
                    <button onClick={runBacktest}>🚀 Run Backtest</button>
                </div>

                {backtestResult && (
                    <div className="macd-section">
                        <h2 className="section-title">📊 Backtest Results</h2>
                        <div
                            className="result-box"
                            dangerouslySetInnerHTML={{ __html: backtestResult }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

export default MACDTrading;
