import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Calendar, DollarSign, Plus, X, Play, Moon, Sun, Info, Trash2, Check } from 'lucide-react';

const MACDTrading = () => {
    // State management
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});
    const [myStocks, setMyStocks] = useState([]);
    const [stockInput, setStockInput] = useState('');
    const [initialBalance, setInitialBalance] = useState(100000);
    const [backtestResult, setBacktestResult] = useState(null);
    const [spyFinalBalance, setSpyFinalBalance] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSpyLoading, setIsSpyLoading] = useState(false);
    const [darkMode, setDarkMode] = useState(false);
    const [showSuccess, setShowSuccess] = useState('');
    const [macdParams, setMacdParams] = useState({
        fastPeriod: 12,
        slowPeriod: 26,
        signalPeriod: 9
    });

    // Mock chart data for demonstration
    const [chartData, setChartData] = useState([]);

    useEffect(() => {
        // Apply dark mode
        if (darkMode) {
            document.body.style.backgroundColor = '#0f1419';
            document.body.style.color = '#ffffff';
        } else {
            document.body.style.backgroundColor = '#ffffff';
            document.body.style.color = '#000000';
        }
    }, [darkMode]);

    // Validation functions
    const validateField = (field, value) => {
        const errors = { ...fieldErrors };
        
        switch (field) {
            case 'startDate':
                if (!value) {
                    errors.startDate = 'Start date is required';
                } else {
                    delete errors.startDate;
                }
                break;
            case 'endDate':
                if (!value) {
                    errors.endDate = 'End date is required';
                } else if (startDate && new Date(value) <= new Date(startDate)) {
                    errors.endDate = 'End date must be after start date';
                } else {
                    delete errors.endDate;
                }
                break;
            case 'initialBalance':
                if (!value || isNaN(value) || Number(value) <= 0) {
                    errors.initialBalance = 'Please enter a valid amount greater than 0';
                } else {
                    delete errors.initialBalance;
                }
                break;
            case 'stocks':
                if (myStocks.length === 0) {
                    errors.stocks = 'Please add at least one stock';
                } else {
                    delete errors.stocks;
                }
                break;
        }
        
        setFieldErrors(errors);
    };

    const isFormValid = () => {
        return startDate && endDate && initialBalance > 0 && 
               new Date(endDate) > new Date(startDate) && 
               Object.keys(fieldErrors).length === 0;
    };

    const isBacktestValid = () => {
        return isFormValid() && myStocks.length > 0;
    };

    // Event handlers
    const handleStartDateChange = (e) => {
        setStartDate(e.target.value);
        validateField('startDate', e.target.value);
        if (endDate) validateField('endDate', endDate);
    };

    const handleEndDateChange = (e) => {
        setEndDate(e.target.value);
        validateField('endDate', e.target.value);
    };

    const handleInitialBalanceChange = (e) => {
        setInitialBalance(e.target.value);
        validateField('initialBalance', e.target.value);
    };

    const handleStockInputChange = (e) => {
        setStockInput(e.target.value.toUpperCase());
    };

    const showSuccessMessage = (message) => {
        setShowSuccess(message);
        setTimeout(() => setShowSuccess(''), 3000);
    };

    const addStock = () => {
        const trimmed = stockInput.trim().toUpperCase();
        if (trimmed && !myStocks.includes(trimmed)) {
            setMyStocks([...myStocks, trimmed]);
            setStockInput('');
            setErrorMessage('');
            validateField('stocks', [...myStocks, trimmed]);
            showSuccessMessage(`${trimmed} added successfully!`);
        } else if (myStocks.includes(trimmed)) {
            setErrorMessage('Stock already added.');
        }
    };

    const deleteStock = (index) => {
        const stockToDelete = myStocks[index];
        const updatedStocks = myStocks.filter((_, i) => i !== index);
        setMyStocks(updatedStocks);
        validateField('stocks', updatedStocks);
        showSuccessMessage(`${stockToDelete} removed`);
    };

    const setDateRange = (range) => {
        const endDate = new Date();
        const startDate = new Date();
        
        switch (range) {
            case '1Y':
                startDate.setFullYear(endDate.getFullYear() - 1);
                break;
            case 'YTD':
                startDate.setMonth(0, 1);
                break;
            case '5Y':
                startDate.setFullYear(endDate.getFullYear() - 5);
                break;
        }
        
        setStartDate(startDate.toISOString().split('T')[0]);
        setEndDate(endDate.toISOString().split('T')[0]);
        validateField('startDate', startDate.toISOString().split('T')[0]);
        validateField('endDate', endDate.toISOString().split('T')[0]);
    };

    const runBacktest = async () => {
        if (!isBacktestValid()) {
            setErrorMessage('Please ensure all fields are valid and at least one stock is selected.');
            return;
        }

        setIsLoading(true);
        setErrorMessage('');

        try {
            // Simulated API call - replace with actual axios call
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Mock response data
            const mockResult = `
                <div class="results-summary">
                    <h3>Strategy Performance</h3>
                    <p><strong>Total Return:</strong> 15.2%</p>
                    <p><strong>Sharpe Ratio:</strong> 1.34</p>
                    <p><strong>Max Drawdown:</strong> -8.1%</p>
                    <p><strong>Win Rate:</strong> 68%</p>
                    <p><strong>Final Balance:</strong> $${(initialBalance * 1.152).toFixed(2)}</p>
                </div>
            `;
            
            // Mock chart data
            const mockChartData = Array.from({ length: 12 }, (_, i) => ({
                month: `Month ${i + 1}`,
                MACD: initialBalance * (1 + (Math.random() * 0.3 - 0.1)),
                SPY: initialBalance * (1 + (Math.random() * 0.2 - 0.05))
            }));

            setBacktestResult(mockResult);
            setChartData(mockChartData);
            showSuccessMessage('Backtest completed successfully!');
        } catch (error) {
            console.error('Error fetching MACD data:', error);
            setErrorMessage('Failed to fetch MACD data');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSpyInvestment = async () => {
        if (!isFormValid()) {
            setErrorMessage('Please enter valid dates and an initial investment amount.');
            return;
        }

        setIsSpyLoading(true);
        setErrorMessage('');

        try {
            // Simulated API call
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            const mockSpyReturn = initialBalance * (1 + Math.random() * 0.2);
            setSpyFinalBalance(mockSpyReturn);
            showSuccessMessage('SPY calculation completed!');
        } catch (error) {
            console.error('Error fetching SPY investment:', error);
            setErrorMessage('Failed to fetch SPY investment data');
        } finally {
            setIsSpyLoading(false);
        }
    };

    return (
        <div className={`min-h-screen transition-colors duration-300 ${
            darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'
        }`}>
            <div className="container mx-auto px-4 py-8 max-w-6xl">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
                    <div>
                        <h1 className="text-3xl sm:text-4xl font-bold flex items-center gap-3">
                            <TrendingUp className="text-blue-500" size={40} />
                            MACD Trading Strategy
                        </h1>
                        <p className={`mt-2 text-lg ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                            Backtest MACD-based trading strategies and compare against SPY performance
                        </p>
                    </div>
                    <button
                        onClick={() => setDarkMode(!darkMode)}
                        className={`p-3 rounded-lg border transition-colors ${
                            darkMode 
                                ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' 
                                : 'bg-white border-gray-300 hover:bg-gray-50'
                        }`}
                    >
                        {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                    </button>
                </div>

                {/* Success Toast */}
                {showSuccess && (
                    <div className="mb-4 p-4 bg-green-100 border border-green-300 text-green-800 rounded-lg flex items-center gap-2">
                        <Check size={20} />
                        {showSuccess}
                    </div>
                )}

                {/* Error Message */}
                {errorMessage && (
                    <div className="mb-4 p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg">
                        {errorMessage}
                    </div>
                )}

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Left Column - Configuration */}
                    <div className="space-y-6">
                        {/* Date Range Section */}
                        <div className={`p-6 rounded-xl border ${
                            darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                        } shadow-lg`}>
                            <div className="flex items-center gap-3 mb-4">
                                <Calendar className="text-blue-500" size={24} />
                                <h2 className="text-xl font-semibold">Date Range</h2>
                            </div>
                            
                            {/* Preset buttons */}
                            <div className="flex flex-wrap gap-2 mb-4">
                                {['1Y', 'YTD', '5Y'].map(range => (
                                    <button
                                        key={range}
                                        onClick={() => setDateRange(range)}
                                        className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors"
                                    >
                                        {range}
                                    </button>
                                ))}
                            </div>

                            <div className="grid sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-2">Start Date</label>
                                    <input
                                        type="date"
                                        value={startDate}
                                        onChange={handleStartDateChange}
                                        className={`w-full p-3 border rounded-lg transition-colors ${
                                            darkMode 
                                                ? 'bg-gray-700 border-gray-600 focus:border-blue-500' 
                                                : 'bg-white border-gray-300 focus:border-blue-500'
                                        } ${fieldErrors.startDate ? 'border-red-500' : ''}`}
                                    />
                                    {fieldErrors.startDate && (
                                        <p className="text-red-500 text-sm mt-1">{fieldErrors.startDate}</p>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-2">End Date</label>
                                    <input
                                        type="date"
                                        value={endDate}
                                        onChange={handleEndDateChange}
                                        className={`w-full p-3 border rounded-lg transition-colors ${
                                            darkMode 
                                                ? 'bg-gray-700 border-gray-600 focus:border-blue-500' 
                                                : 'bg-white border-gray-300 focus:border-blue-500'
                                        } ${fieldErrors.endDate ? 'border-red-500' : ''}`}
                                    />
                                    {fieldErrors.endDate && (
                                        <p className="text-red-500 text-sm mt-1">{fieldErrors.endDate}</p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Investment Amount Section */}
                        <div className={`p-6 rounded-xl border ${
                            darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                        } shadow-lg`}>
                            <div className="flex items-center gap-3 mb-4">
                                <DollarSign className="text-green-500" size={24} />
                                <h2 className="text-xl font-semibold">Investment Amount</h2>
                                <div className="group relative">
                                    <Info size={16} className="text-gray-400 cursor-help" />
                                    <div className="absolute bottom-6 left-0 hidden group-hover:block bg-black text-white text-xs p-2 rounded whitespace-nowrap">
                                        Used for both MACD strategy and SPY comparison
                                    </div>
                                </div>
                            </div>
                            
                            <input
                                type="number"
                                value={initialBalance}
                                onChange={handleInitialBalanceChange}
                                placeholder="e.g., 100000"
                                className={`w-full p-3 border rounded-lg mb-4 transition-colors ${
                                    darkMode 
                                        ? 'bg-gray-700 border-gray-600 focus:border-blue-500' 
                                        : 'bg-white border-gray-300 focus:border-blue-500'
                                } ${fieldErrors.initialBalance ? 'border-red-500' : ''}`}
                            />
                            {fieldErrors.initialBalance && (
                                <p className="text-red-500 text-sm mb-4">{fieldErrors.initialBalance}</p>
                            )}

                            <button
                                onClick={handleSpyInvestment}
                                disabled={!isFormValid() || isSpyLoading}
                                className={`w-full p-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
                                    !isFormValid() || isSpyLoading
                                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                        : 'bg-green-500 text-white hover:bg-green-600 transform hover:scale-105'
                                }`}
                            >
                                {isSpyLoading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                                        Calculating...
                                    </>
                                ) : (
                                    <>
                                        <DollarSign size={20} />
                                        Calculate SPY Investment
                                    </>
                                )}
                            </button>

                            {spyFinalBalance !== null && (
                                <div className={`mt-4 p-4 rounded-lg border-l-4 border-green-500 ${
                                    darkMode ? 'bg-gray-700' : 'bg-green-50'
                                }`}>
                                    <h3 className="font-semibold text-green-600">SPY Investment Results</h3>
                                    <div className="flex justify-between mt-2">
                                        <span>Initial Investment:</span>
                                        <span className="font-semibold">${Number(initialBalance).toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Final Balance:</span>
                                        <span className="font-semibold text-green-600">
                                            ${Number(spyFinalBalance).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Return:</span>
                                        <span className={`font-semibold ${
                                            spyFinalBalance > initialBalance ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                            {(((spyFinalBalance - initialBalance) / initialBalance) * 100).toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* MACD Parameters */}
                        <div className={`p-6 rounded-xl border ${
                            darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                        } shadow-lg`}>
                            <h3 className="text-lg font-semibold mb-4">MACD Parameters</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Fast Period: {macdParams.fastPeriod}
                                    </label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="20"
                                        value={macdParams.fastPeriod}
                                        onChange={(e) => setMacdParams({...macdParams, fastPeriod: e.target.value})}
                                        className="w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Slow Period: {macdParams.slowPeriod}
                                    </label>
                                    <input
                                        type="range"
                                        min="20"
                                        max="35"
                                        value={macdParams.slowPeriod}
                                        onChange={(e) => setMacdParams({...macdParams, slowPeriod: e.target.value})}
                                        className="w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Signal Period: {macdParams.signalPeriod}
                                    </label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="15"
                                        value={macdParams.signalPeriod}
                                        onChange={(e) => setMacdParams({...macdParams, signalPeriod: e.target.value})}
                                        className="w-full"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Stock Selection Section */}
                        <div className={`p-6 rounded-xl border ${
                            darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                        } shadow-lg`}>
                            <h2 className="text-xl font-semibold mb-4">Stock Selection</h2>
                            
                            <div className="flex gap-2 mb-4">
                                <input
                                    type="text"
                                    value={stockInput}
                                    onChange={handleStockInputChange}
                                    placeholder="Enter stock symbol (e.g., AAPL)"
                                    className={`flex-1 p-3 border rounded-lg transition-colors ${
                                        darkMode 
                                            ? 'bg-gray-700 border-gray-600 focus:border-blue-500' 
                                            : 'bg-white border-gray-300 focus:border-blue-500'
                                    }`}
                                    onKeyPress={(e) => e.key === 'Enter' && addStock()}
                                />
                                <button
                                    onClick={addStock}
                                    disabled={!stockInput.trim() || myStocks.includes(stockInput.trim().toUpperCase())}
                                    className={`px-4 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${
                                        !stockInput.trim() || myStocks.includes(stockInput.trim().toUpperCase())
                                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                            : 'bg-blue-500 text-white hover:bg-blue-600 transform hover:scale-105'
                                    }`}
                                >
                                    <Plus size={20} />
                                    Add
                                </button>
                            </div>

                            {/* Stock Chips */}
                            <div className="flex flex-wrap gap-2 mb-4">
                                {myStocks.map((stock, idx) => (
                                    <span
                                        key={idx}
                                        className="inline-flex items-center gap-2 px-3 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium transition-all hover:bg-blue-200"
                                    >
                                        {stock}
                                        <button
                                            onClick={() => deleteStock(idx)}
                                            className="hover:bg-blue-300 rounded-full p-1 transition-colors"
                                        >
                                            <X size={14} />
                                        </button>
                                    </span>
                                ))}
                            </div>

                            {fieldErrors.stocks && (
                                <p className="text-red-500 text-sm mb-4">{fieldErrors.stocks}</p>
                            )}

                            <button
                                onClick={runBacktest}
                                disabled={!isBacktestValid() || isLoading}
                                className={`w-full p-4 rounded-lg font-semibold text-lg transition-all flex items-center justify-center gap-3 ${
                                    !isBacktestValid() || isLoading
                                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                        : 'bg-gradient-to-r from-purple-500 to-blue-600 text-white hover:from-purple-600 hover:to-blue-700 transform hover:scale-105'
                                }`}
                            >
                                {isLoading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent"></div>
                                        Running Backtest...
                                    </>
                                ) : (
                                    <>
                                        <Play size={24} />
                                        Run Backtest
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Right Column - Results */}
                    <div className="space-y-6">
                        {/* Chart Section */}
                        {chartData.length > 0 && (
                            <div className={`p-6 rounded-xl border ${
                                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                            } shadow-lg`}>
                                <h3 className="text-xl font-semibold mb-4">Performance Comparison</h3>
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
                                            <XAxis 
                                                dataKey="month" 
                                                stroke={darkMode ? '#9ca3af' : '#6b7280'}
                                            />
                                            <YAxis 
                                                stroke={darkMode ? '#9ca3af' : '#6b7280'}
                                                tickFormatter={(value) => `$${(value/1000).toFixed(0)}K`}
                                            />
                                            <Tooltip 
                                                formatter={(value) => [`$${Number(value).toLocaleString()}`, '']}
                                                contentStyle={{
                                                    backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                                                    border: `1px solid ${darkMode ? '#374151' : '#d1d5db'}`,
                                                    borderRadius: '8px'
                                                }}
                                            />
                                            <Legend />
                                            <Line 
                                                type="monotone" 
                                                dataKey="MACD" 
                                                stroke="#8b5cf6" 
                                                strokeWidth={3}
                                                name="MACD Strategy"
                                            />
                                            <Line 
                                                type="monotone" 
                                                dataKey="SPY" 
                                                stroke="#10b981" 
                                                strokeWidth={3}
                                                name="SPY Buy & Hold"
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}

                        {/* Results Section */}
                        {backtestResult && (
                            <div className={`p-6 rounded-xl border ${
                                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                            } shadow-lg`}>
                                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                    📊 Backtest Results
                                </h2>
                                <div
                                    className={`p-4 rounded-lg ${
                                        darkMode ? 'bg-gray-700' : 'bg-gray-50'
                                    }`}
                                    dangerouslySetInnerHTML={{ __html: backtestResult }}
                                />
                            </div>
                        )}

                        {/* Placeholder when no results */}
                        {!backtestResult && !isLoading && (
                            <div className={`p-8 rounded-xl border-2 border-dashed ${
                                darkMode ? 'border-gray-600 text-gray-400' : 'border-gray-300 text-gray-500'
                            } text-center`}>
                                <TrendingUp size={48} className="mx-auto mb-4 opacity-50" />
                                <p className="text-lg">Configure your strategy and run a backtest to see results here</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MACDTrading;