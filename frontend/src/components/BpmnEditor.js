import React, { useEffect, useRef, useState } from 'react';
import BpmnJS from 'bpmn-js/lib/Modeler';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Default BPMN diagram template
const defaultBpmnXML = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn2:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bpmn2="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xsi:schemaLocation="http://www.omg.org/spec/BPMN/20100524/MODEL BPMN20.xsd" id="sample-diagram" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn2:process id="Process_1" isExecutable="false">
    <bpmn2:startEvent id="StartEvent_1"/>
  </bpmn2:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds height="36.0" width="36.0" x="412.0" y="240.0"/>
      </bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn2:definitions>`;

const BpmnEditor = ({ currentProcess, onSave, onClose }) => {
  const containerRef = useRef(null);
  const bpmnModelerRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [processName, setProcessName] = useState(currentProcess?.name || 'Untitled Process');
  const [processDescription, setProcessDescription] = useState(currentProcess?.description || '');

  useEffect(() => {
    if (containerRef.current && !bpmnModelerRef.current) {
      // Initialize BPMN Modeler
      bpmnModelerRef.current = new BpmnJS({
        container: containerRef.current,
        keyboard: {
          bindTo: window
        },
        moddleExtensions: {}
      });

      // Load the diagram
      loadDiagram();
    }

    return () => {
      if (bpmnModelerRef.current) {
        bpmnModelerRef.current.destroy();
        bpmnModelerRef.current = null;
      }
    };
  }, [currentProcess]);

  const loadDiagram = async () => {
    if (!bpmnModelerRef.current) return;
    
    setLoading(true);
    try {
      const xmlToLoad = currentProcess?.bpmn_xml || defaultBpmnXML;
      await bpmnModelerRef.current.importXML(xmlToLoad);
      
      // Fit viewport to diagram content
      const canvas = bpmnModelerRef.current.get('canvas');
      canvas.zoom('fit-viewport');
    } catch (error) {
      console.error('Error loading BPMN diagram:', error);
      // If loading fails, load default template
      await bpmnModelerRef.current.importXML(defaultBpmnXML);
    } finally {
      setLoading(false);
    }
  };

  const saveProcess = async () => {
    if (!bpmnModelerRef.current) return;
    
    setSaving(true);
    try {
      // Export the current BPMN XML
      const { xml } = await bpmnModelerRef.current.saveXML({ format: true });
      
      const processData = {
        name: processName,
        description: processDescription,
        bpmn_xml: xml
      };

      let response;
      if (currentProcess?.isNew || !currentProcess?.id) {
        // Create new process
        response = await axios.post(`${API}/processes`, processData);
      } else {
        // Update existing process
        response = await axios.put(`${API}/processes/${currentProcess.id}`, processData);
      }

      console.log('Process saved:', response.data);
      onSave && onSave();
    } catch (error) {
      console.error('Error saving process:', error);
      alert('Error saving process. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const exportBpmn = async () => {
    if (!bpmnModelerRef.current) return;
    
    try {
      const { xml } = await bpmnModelerRef.current.saveXML({ format: true });
      const blob = new Blob([xml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${processName}.bpmn`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting BPMN:', error);
    }
  };

  const importBpmn = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const xml = e.target.result;
        await bpmnModelerRef.current.importXML(xml);
        const canvas = bpmnModelerRef.current.get('canvas');
        canvas.zoom('fit-viewport');
      } catch (error) {
        console.error('Error importing BPMN:', error);
        alert('Error importing BPMN file. Please check the file format.');
      }
    };
    reader.readAsText(file);
    event.target.value = ''; // Reset file input
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex flex-col">
            <input
              type="text"
              value={processName}
              onChange={(e) => setProcessName(e.target.value)}
              className="text-lg font-semibold border-none outline-none p-1 rounded"
              placeholder="Process Name"
            />
            <input
              type="text"
              value={processDescription}
              onChange={(e) => setProcessDescription(e.target.value)}
              className="text-sm text-gray-600 border-none outline-none p-1 rounded"
              placeholder="Process Description"
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors">
            Import BPMN
            <input
              type="file"
              accept=".bpmn,.xml"
              onChange={importBpmn}
              className="hidden"
            />
          </label>
          
          <button
            onClick={exportBpmn}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Export BPMN
          </button>
          
          <button
            onClick={saveProcess}
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center"
          >
            {saving ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </>
            ) : (
              'Save Process'
            )}
          </button>
          
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* BPMN Canvas */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
            <div className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading BPMN Editor...
            </div>
          </div>
        )}
        <div ref={containerRef} className="h-full w-full" />
      </div>
    </div>
  );
};

export default BpmnEditor;