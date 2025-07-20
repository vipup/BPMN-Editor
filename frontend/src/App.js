import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import BpmnEditor from './components/BpmnEditor';
import ProcessList from './components/ProcessList';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [processes, setProcesses] = useState([]);
  const [currentProcess, setCurrentProcess] = useState(null);

  const fetchProcesses = async () => {
    try {
      const response = await axios.get(`${API}/processes`);
      setProcesses(response.data);
    } catch (error) {
      console.error('Error fetching processes:', error);
    }
  };

  useEffect(() => {
    fetchProcesses();
  }, []);

  const createNewProcess = () => {
    const newProcess = {
      id: Date.now().toString(),
      name: `New Process ${Date.now()}`,
      description: 'A new business process',
      bpmn_xml: null,
      created_at: new Date().toISOString(),
      isNew: true
    };
    setCurrentProcess(newProcess);
  };

  return (
    <div className="App min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <BrowserRouter>
        <nav className="bg-white shadow-lg border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link to="/" className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                    </svg>
                  </div>
                  <h1 className="ml-3 text-xl font-bold text-gray-900">BPMN Flow Editor</h1>
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link 
                  to="/" 
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Processes
                </Link>
                <button
                  onClick={createNewProcess}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm"
                >
                  New Process
                </button>
              </div>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={
            <ProcessList 
              processes={processes} 
              onRefresh={fetchProcesses}
              onSelectProcess={setCurrentProcess}
            />
          } />
          <Route path="/editor/:id?" element={
            <BpmnEditor 
              currentProcess={currentProcess}
              onSave={fetchProcesses}
            />
          } />
        </Routes>

        {currentProcess && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div className="bg-white p-1 rounded-lg shadow-xl w-full h-full">
              <div className="flex justify-between items-center p-4 border-b">
                <h2 className="text-lg font-semibold">{currentProcess.name}</h2>
                <button 
                  onClick={() => setCurrentProcess(null)}
                  className="text-gray-500 hover:text-gray-700 p-1"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="h-full">
                <BpmnEditor 
                  currentProcess={currentProcess}
                  onSave={() => {
                    fetchProcesses();
                    setCurrentProcess(null);
                  }}
                  onClose={() => setCurrentProcess(null)}
                />
              </div>
            </div>
          </div>
        )}
      </BrowserRouter>
    </div>
  );
}

export default App;