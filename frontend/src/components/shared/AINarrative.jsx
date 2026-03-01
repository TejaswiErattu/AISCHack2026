import React, { useState, useEffect } from 'react';

const AINarrative = ({ text, mode = 'clinical' }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);

  // Mode styling configurations
  const modes = {
    clinical: {
      border: 'border-l-[3px] border-accent-financial',
      label: 'Underwriting Intelligence',
      icon: '💼'
    },
    empathetic: {
      border: 'border-l-[3px] border-accent-positive',
      label: 'TerraLend Assistant',
      icon: '🌿'
    },
    technical: {
      border: 'border-l-[3px] border-purple-500',
      label: 'Climate Analysis Core',
      icon: '🔬'
    }
  };

  const currentMode = modes[mode];

  useEffect(() => {
    setDisplayedText('');
    setIsTyping(true);
    let i = 0;
    const interval = setInterval(() => {
      setDisplayedText((prev) => prev + text.charAt(i));
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 15); // Fast typing effect
    return () => clearInterval(interval);
  }, [text, mode]);

  return (
    <div className={`bg-background-secondary/50 p-5 rounded-card border border-border ${currentMode.border} transition-all duration-500`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">{currentMode.icon}</span>
        <span className="text-[11px] font-bold text-text-primary uppercase tracking-widest">
          {currentMode.label}
        </span>
      </div>
      <p className="text-[14px] text-text-secondary leading-relaxed min-h-[80px]">
        {displayedText}
        {isTyping && <span className="inline-block w-1.5 h-4 ml-1 bg-accent-primary animate-pulse align-middle" />}
      </p>
    </div>
  );
};

export default AINarrative;