import { useState } from 'react'
import MainScreen from './screens/MainScreen'
import MovingAverages from './screens/MovingAverages'
import RSITrading from './screens/RSI'
import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

function App() {
  console.log('Hello')

  return (
    <div className="app">
        <div className = "content">
          <Routes>
            <Route path="/" element={<MainScreen />} />
            <Route path="/moving-averages" element={<MovingAverages />} />
            <Route path ="/RSI-trading" element={<RSITrading />} />
          </Routes>
        </div>
      </div>
  );
}

export default App
