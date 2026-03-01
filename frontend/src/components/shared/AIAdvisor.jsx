import React, { useState, useEffect, useContext, useRef } from 'react';
import { AppContext } from '../../context/AppContext';

const AIAdvisor = ({ panel }) => {
  const { financialOutputs, climateData, selectedRegion } = useContext(AppContext);
  const [questions, setQuestions] = useState([]);
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [isResponding, setIsResponding] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation, isResponding]);

  useEffect(() => {
    if (!selectedRegion) return;

    const generateQuestions = async () => {
      setIsGeneratingQuestions(true);
      try {
        const response = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            system: "",
            messages: [{
              role: "user",
              content: `Given this farm data, generate exactly 3 short questions (max 10 words each) that a ${panel} would want to ask. Data: stress=${climateData.yield_stress_score}, rate=${financialOutputs.interest_rate}%, crop=${selectedRegion.primary_crop}, region=${selectedRegion.name}, drought=${climateData.drought_index}, ndvi=${climateData.ndvi_score}. Question 1: about why current situation is what it is. Question 2: about what would improve the outcome. Question 3: about risk or what makes it worse. Return ONLY a JSON array of 3 strings, no preamble.`
            }]
          })
        });
        const data = await response.json();
        const questionsArr = JSON.parse(data.text.replace(/```json|```/g, '').trim());
        setQuestions(questionsArr);
      } catch (err) {
        console.error("Failed to generate questions", err);
      } finally {
        setIsGeneratingQuestions(false);
      }
    };

    generateQuestions();
    setConversation([]);
  }, [selectedRegion, panel]);

  const askQuestion = async (text) => {
    if (conversation.length >= 6) return;

    const newHistory = [...conversation, { role: 'user', content: text }];
    setConversation(newHistory);
    setQuestions([]);
    setIsResponding(true);

    const systemPrompts = {
      loan_officer: `You are TerraLend's AI underwriting assistant speaking to a loan officer. Be clinical, precise, data-referenced. Current context — Region: ${selectedRegion.name}, Crop: ${selectedRegion.primary_crop}, Yield Stress: ${climateData.yield_stress_score}/100, Heat: +${climateData.temperature_anomaly}°C, Drought: ${climateData.drought_index}/100, NDVI: ${climateData.ndvi_score}/100, Rate: ${financialOutputs.interest_rate}%, PD: ${financialOutputs.probability_of_default * 100}%. Max 4 sentences.`,
      farmer: `You are TerraLend's farmer advisor. Speak warmly and plainly — no jargon. You are on the farmer's side. Current context — Farm: ${selectedRegion.name}, Crop: ${selectedRegion.primary_crop}, Their rate: ${financialOutputs.interest_rate}%, Old system rate: ${financialOutputs.baseline_rate}%, Stress level: ${climateData.yield_stress_score}/100. Answer like you're at a kitchen table. Max 3 sentences.`,
      scientist: `You are TerraLend's climate analysis engine speaking to a climate scientist. Be technically precise, cite index names, use quantitative reasoning. Current context — Region: ${selectedRegion.name} (${selectedRegion.lat}°N), Crop: ${selectedRegion.primary_crop}, Heat stress: ${climateData.temperature_anomaly}°C anomaly, Drought index: ${climateData.drought_index}/100, NDVI: ${climateData.ndvi_score}/100, Soil moisture: ${climateData.soil_moisture}/100, Composite stress: ${climateData.yield_stress_score}/100. Max 5 sentences.`
    };

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: systemPrompts[panel],
          messages: newHistory
        })
      });
      const data = await response.json();
      setConversation([...newHistory, { role: 'assistant', content: data.text }]);
    } catch (err) {
      console.error("Chat error", err);
    } finally {
      setIsResponding(false);
    }
  };

  if (!selectedRegion) return null;

  const isTerminal = panel === 'loan_officer' || panel === 'scientist';

  return (
    <div className={`w-full ${isTerminal ? 'border-t border-[#1a1a1a] mt-3 pt-3' : 'border-t border-white/10 mt-3 pt-3'}`}>

      {/* 1. Suggested Question Chips */}
      <div className="flex flex-wrap gap-2 mb-3">
        {isGeneratingQuestions ? (
          [1, 2, 3].map(i => (
            <div key={i} className="h-6 w-32 bg-[#1a1a1a] animate-pulse rounded-sm" />
          ))
        ) : (
          questions.map((q, i) => (
            <button
              key={i}
              onClick={() => askQuestion(q)}
              className={isTerminal
                ? "bg-[#111] border border-[#333] text-[#475569] font-mono text-[10px] px-2 py-1 hover:border-[#00D4AA] hover:text-[#00D4AA] transition-colors"
                : "bg-[#1E2D45] rounded-full text-[#94A3B8] text-[12px] px-3 py-1 hover:bg-[#00D4AA]/10 hover:text-[#00D4AA] transition-colors"
              }
            >
              {q}
            </button>
          ))
        )}
      </div>

      {/* 2. Chat History */}
      <div className="space-y-3 overflow-y-auto max-h-[250px] pr-1">
        {conversation.map((msg, i) => (
          <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <p className={`
              ${panel === 'farmer' ? 'text-[13px]' : 'font-mono text-[11px]'}
              ${msg.role === 'user'
                ? (panel === 'farmer' ? 'text-[#00D4AA]' : 'text-[#F1F5F9]')
                : (panel === 'farmer' ? 'text-[#F1F5F9]' : 'text-[#94A3B8]')}
            `}>
              {msg.role === 'assistant' && isTerminal && '> '}
              {msg.role === 'user' && panel === 'scientist' && 'QUERY: '}
              {msg.content}
            </p>
          </div>
        ))}
        {isResponding && (
          <span className="text-[#00D4AA] animate-pulse font-mono text-[11px] ml-1">█</span>
        )}
        {conversation.length >= 6 && (
          <p className="text-[#EF4444] font-mono text-[10px] uppercase opacity-70 mt-2">
            {isTerminal ? '> SESSION_LIMIT — start new analysis' : 'Session limit reached.'}
          </p>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* 3. Input Area */}
      {conversation.length < 6 && (
        <div className="mt-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && inputValue.trim()) {
                askQuestion(inputValue);
                setInputValue('');
              }
            }}
            placeholder={isTerminal ? "TYPE QUERY..." : "Ask a follow-up..."}
            className={`
              w-full outline-none transition-all
              ${isTerminal
                ? 'bg-transparent border-t border-[#1a1a1a] font-mono text-[11px] text-[#F1F5F9] pt-2'
                : 'bg-[#1E2D45] rounded-lg px-3 py-2 text-[13px] text-white'}
            `}
          />
        </div>
      )}
    </div>
  );
};

export default AIAdvisor;