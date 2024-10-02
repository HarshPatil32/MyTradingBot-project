import { useState } from 'react'
import MainScreen from './screens/MainScreen'
import './App.css'
import { Routes, Route } from 'react-router-dom'

function App() {
  console.log('Hello')

  return (
    <div className="app">
        <div className = "content">
          <Routes>
            <Route path="/" element={<MainScreen />} />
          </Routes>
        </div>
      </div>
  );
}

export default App
