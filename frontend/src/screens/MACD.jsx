import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Calendar, DollarSign, Plus, X, Play, Moon, Sun, Info, Trash2, Check, Settings } from 'lucide-react';
import axios from 'axios';

const MACDTrading = () => {
    // API URL from environment variables
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';
    
    // Debug: Log API URL
    console.log('API_URL:', API_URL);
    console.log('Environment variables:', import.meta.env);
    
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
    const [darkMode, setDarkMode] = useState(false);
    const [showSuccess, setShowSuccess] = useState('');
    const [optimizedParams, setOptimizedParams] = useState(null);
    const [optimizationPerformance, setOptimizationPerformance] = useState(null);
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
            // Call both MACD strategy and SPY investment in parallel
            const [macdResponse, spyResponse] = await Promise.all([
                axios.get(`${API_URL}/MACD-strategy`, {
                    params: {
                        stocks: myStocks.join(','),
                        start_date: startDate,
                        end_date: endDate,
                        initial_balance: initialBalance,
                        optimize: 'true'
                    }
                }),
                axios.get(`${API_URL}/spy-investment`, {
                    params: {
                        start_date: startDate,
                        end_date: endDate,
                        initial_balance: initialBalance
                    }
                })
            ]);

            // Handle MACD response
            if (macdResponse.data.error) {
                setErrorMessage(macdResponse.data.error);
                return;
            }

            // Handle SPY response
            if (spyResponse.data.error) {
                setErrorMessage(spyResponse.data.error);
                return;
            }

            // Set the optimized parameters
            if (macdResponse.data.optimized_parameters) {
                setOptimizedParams(macdResponse.data.optimized_parameters);
                setOptimizationPerformance(macdResponse.data.optimization_performance);
                setMacdParams({
                    fastPeriod: macdResponse.data.optimized_parameters.fastperiod,
                    slowPeriod: macdResponse.data.optimized_parameters.slowperiod,
                    signalPeriod: macdResponse.data.optimized_parameters.signalperiod
                });
            }

            // Set backtest result
            const backtestResult = macdResponse.data.backtest_result || macdResponse.data;
            setBacktestResult(backtestResult);

            // Set SPY final balance
            setSpyFinalBalance(spyResponse.data.final_balance);

            // Use real monthly performance data from backend
            const generateChartData = () => {
                const macdMonthlyData = macdResponse.data.monthly_performance;
                const spyMonthlyData = spyResponse.data.monthly_performance;
                
                if (macdMonthlyData && spyMonthlyData) {
                    // Combine both datasets for chart
                    const maxLength = Math.max(macdMonthlyData.length, spyMonthlyData.length);
                    const chartData = [];
                    
                    for (let i = 0; i < maxLength; i++) {
                        const macdPoint = macdMonthlyData[i] || macdMonthlyData[macdMonthlyData.length - 1];
                        const spyPoint = spyMonthlyData[i] || spyMonthlyData[spyMonthlyData.length - 1];
                        
                        chartData.push({
                            month: macdPoint.month,
                            MACD: Math.round(macdPoint.balance),
                            SPY: Math.round(spyPoint.balance)
                        });
                    }
                    
                    return chartData;
                } else {
                    // Fallback to simple calculation if no monthly data
                    const optimizationPerf = macdResponse.data.optimization_performance;
                    if (optimizationPerf && spyResponse.data.final_balance) {
                        const dataPoints = 12;
                        const chartData = [];
                        const macdFinalBalance = optimizationPerf.best_balance;
                        const spyFinalBalance = spyResponse.data.final_balance;
                        
                        const macdTotalReturn = (macdFinalBalance - initialBalance) / initialBalance;
                        const spyTotalReturn = (spyFinalBalance - initialBalance) / initialBalance;
                        
                        const macdMonthlyReturn = Math.pow(1 + macdTotalReturn, 1/dataPoints) - 1;
                        const spyMonthlyReturn = Math.pow(1 + spyTotalReturn, 1/dataPoints) - 1;
                        
                        let macdBalance = initialBalance;
                        let spyBalance = initialBalance;
                        
                        for (let i = 0; i <= dataPoints; i++) {
                            chartData.push({
                                month: i === 0 ? 'Start' : `Month ${i}`,
                                MACD: Math.round(macdBalance),
                                SPY: Math.round(spyBalance)
                            });
                            
                            if (i < dataPoints) {
                                macdBalance *= (1 + macdMonthlyReturn);
                                spyBalance *= (1 + spyMonthlyReturn);
                                
                                macdBalance = Math.max(macdBalance, initialBalance * 0.5);
                                spyBalance = Math.max(spyBalance, initialBalance * 0.5);
                            }
                        }
                        
                        // Adjust final values to match actual results
                        chartData[chartData.length - 1].MACD = Math.round(macdFinalBalance);
                        chartData[chartData.length - 1].SPY = Math.round(spyFinalBalance);
                        
                        return chartData;
                    } else {
                        // Ultimate fallback
                        return [{
                            month: 'Start',
                            MACD: initialBalance,
                            SPY: initialBalance
                        }];
                    }
                }
            };

            setChartData(generateChartData());
            showSuccessMessage('MACD optimization completed and compared with SPY performance!');
        } catch (error) {
            console.error('Error fetching MACD data:', error);
            if (error.response) {
                setErrorMessage(`Server error: ${error.response.data.error || 'Unknown error'}`);
            } else if (error.request) {
                setErrorMessage('Unable to connect to server. Please ensure the backend is running.');
            } else {
                setErrorMessage('Failed to fetch MACD data');
            }
        } finally {
            setIsLoading(false);
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
                                className={`w-full p-3 border rounded-lg transition-colors ${
                                    darkMode 
                                        ? 'bg-gray-700 border-gray-600 focus:border-blue-500' 
                                        : 'bg-white border-gray-300 focus:border-blue-500'
                                } ${fieldErrors.initialBalance ? 'border-red-500' : ''}`}
                            />
                            {fieldErrors.initialBalance && (
                                <p className="text-red-500 text-sm">{fieldErrors.initialBalance}</p>
                            )}
                        </div>

                        {/* MACD Parameters */}
                        <div className={`p-6 rounded-xl border ${
                            darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                        } shadow-lg`}>
                            <div className="flex items-center gap-3 mb-4">
                                <Settings className="text-purple-500" size={24} />
                                <h3 className="text-lg font-semibold">MACD Parameters</h3>
                                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                    Auto-Optimized
                                </span>
                            </div>
                            
                            <div className={`p-4 rounded-lg border-l-4 border-blue-500 ${
                                darkMode ? 'bg-gray-700' : 'bg-blue-50'
                            }`}>
                                <h4 className="font-semibold text-blue-600 mb-2">
                                    {optimizedParams ? 'Optimized Parameters' : 'Default Parameters (Will be optimized on backtest)'}
                                </h4>
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <span className="font-medium">Fast Period:</span>
                                        <div className="text-lg font-bold text-blue-600">
                                            {optimizedParams ? optimizedParams.fastperiod : macdParams.fastPeriod}
                                        </div>
                                    </div>
                                    <div>
                                        <span className="font-medium">Slow Period:</span>
                                        <div className="text-lg font-bold text-blue-600">
                                            {optimizedParams ? optimizedParams.slowperiod : macdParams.slowPeriod}
                                        </div>
                                    </div>
                                    <div>
                                        <span className="font-medium">Signal Period:</span>
                                        <div className="text-lg font-bold text-blue-600">
                                            {optimizedParams ? optimizedParams.signalperiod : macdParams.signalPeriod}
                                        </div>
                                    </div>
                                </div>
                                <p className="text-xs text-gray-600 mt-2">
                                    Parameters are automatically optimized using Bayesian optimization to maximize returns
                                </p>
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
                                        Running Optimization & Backtest...
                                    </>
                                ) : (
                                    <>
                                        <Play size={24} />
                                        <span className="flex flex-col items-center">
                                            <span>Run MACD Backtest</span>
                                            <span className="text-xs opacity-80">Auto-optimizes parameters & compares with SPY</span>
                                        </span>
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
                            <div className="space-y-6">
                                {/* Performance Summary */}
                                {spyFinalBalance !== null && (
                                    <div className={`p-6 rounded-xl border ${
                                        darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                                    } shadow-lg`}>
                                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                            📈 Performance Summary
                                        </h2>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* MACD Strategy Results */}
                                            <div className={`p-4 rounded-lg border-l-4 border-purple-500 ${
                                                darkMode ? 'bg-gray-700' : 'bg-purple-50'
                                            }`}>
                                                <h3 className="font-semibold text-purple-600 mb-2">MACD Strategy (Optimized)</h3>
                                                <div className="space-y-1 text-sm">
                                                    <div className="flex justify-between">
                                                        <span>Initial Investment:</span>
                                                        <span className="font-semibold">${Number(initialBalance).toLocaleString()}</span>
                                                    </div>
                                                    <div className="flex justify-between">
                                                        <span>Final Balance:</span>
                                                        <span className="font-semibold text-purple-600">
                                                            ${optimizationPerformance ? Number(optimizationPerformance.best_balance).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'N/A'}
                                                        </span>
                                                    </div>
                                                    <div className="flex justify-between">
                                                        <span>Return:</span>
                                                        <span className={`font-semibold ${
                                                            optimizationPerformance && optimizationPerformance.best_balance > initialBalance ? 'text-green-600' : 'text-red-600'
                                                        }`}>
                                                            {optimizationPerformance ? 
                                                                optimizationPerformance.total_return.toFixed(2) + '%' 
                                                                : 'N/A'}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* SPY Results */}
                                            <div className={`p-4 rounded-lg border-l-4 border-green-500 ${
                                                darkMode ? 'bg-gray-700' : 'bg-green-50'
                                            }`}>
                                                <h3 className="font-semibold text-green-600 mb-2">SPY Buy & Hold</h3>
                                                <div className="space-y-1 text-sm">
                                                    <div className="flex justify-between">
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
                                            </div>
                                        </div>

                                        {/* Strategy Comparison */}
                                        {optimizationPerformance && (
                                            <div className={`mt-6 p-4 rounded-lg ${
                                                optimizationPerformance.best_balance > spyFinalBalance 
                                                    ? 'bg-green-100 border border-green-300' 
                                                    : 'bg-red-100 border border-red-300'
                                            }`}>
                                                <div className="flex items-center justify-between">
                                                    <span className="font-semibold">
                                                        {optimizationPerformance.best_balance > spyFinalBalance 
                                                            ? '🎉 MACD Strategy Outperformed SPY!' 
                                                            : '📉 SPY Outperformed MACD Strategy'}
                                                    </span>
                                                    <span className={`font-bold text-lg ${
                                                        optimizationPerformance.best_balance > spyFinalBalance ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                        {optimizationPerformance.best_balance > spyFinalBalance ? '+' : ''}
                                                        ${(optimizationPerformance.best_balance - spyFinalBalance).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Detailed Backtest Results */}
                                <div className={`p-6 rounded-xl border ${
                                    darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                                } shadow-lg`}>
                                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                        📊 Detailed Backtest Results
                                    </h2>
                                    <div
                                        className={`p-4 rounded-lg ${
                                            darkMode ? 'bg-gray-700' : 'bg-gray-50'
                                        }`}
                                        dangerouslySetInnerHTML={{ __html: backtestResult }}
                                    />
                                </div>
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