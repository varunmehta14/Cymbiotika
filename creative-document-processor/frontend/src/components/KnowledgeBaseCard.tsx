"use client";

import React from "react";
import clsx from "clsx";

type KnowledgeBaseProps = {
  kb: {
    id: string;
    name: string;
    description: string;
    icon: React.ReactNode;
    color?: string;
  };
  selected: boolean;
  onSelect: () => void;
  colorGradient?: string;
  animationDelay?: number;
};

const KnowledgeBaseCard: React.FC<KnowledgeBaseProps> = ({
  kb,
  selected,
  onSelect,
  colorGradient = "from-primary-600 to-primary-500",
  animationDelay = 0,
}) => {
  // Extract the color base from the gradient (e.g., "blue" from "from-blue-500")
  const colorBase = colorGradient.split('-')[1];
  
  return (
    <div
      className={clsx(
        "p-6 rounded-xl cursor-pointer transition-all duration-300 animate-slide-in-bottom backdrop-blur-sm",
        {
          "shadow-lg bg-white/90 border border-white/50": !selected,
          "ring-[3px] ring-offset-2 ring-offset-slate-50 shadow-xl glass-effect transform scale-[1.03] border-0": selected,
          "hover:shadow-xl hover:scale-[1.02] hover:bg-white": !selected,
        }
      )}
      style={{ 
        animationDelay: `${animationDelay}ms`,
        ...(selected ? { 
          boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
          ringColor: colorBase === "blue" ? "#3b82f6" : 
                     colorBase === "green" ? "#10b981" : 
                     colorBase === "orange" ? "#f97316" : 
                     colorBase === "purple" ? "#8b5cf6" : 
                     "#0284c7" // default to primary-600
        } : {})
      }}
      onClick={onSelect}
    >
      <div className="flex flex-col gap-4">
        <div
          className={clsx("rounded-full p-3 w-fit", {
            [`bg-gradient-to-r ${colorGradient} text-white shadow-md`]: selected,
            "bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors": !selected,
          })}
        >
          {kb.icon}
        </div>
        <div>
          <h3 className={clsx("text-lg font-semibold mb-2", {
            "text-transparent bg-clip-text bg-gradient-to-r": selected,
            [colorGradient]: selected,
            "text-slate-900": !selected
          })}>
            {kb.name}
          </h3>
          <p className="text-sm text-slate-600">{kb.description}</p>
        </div>
        
        {/* Selection indicator */}
        {selected && (
          <div 
            className="w-full rounded-md p-2 mt-2 text-xs font-medium flex items-center justify-center"
            style={{
              backgroundColor: `rgba(${
                colorBase === "blue" ? "59, 130, 246, 0.1" : 
                colorBase === "green" ? "16, 185, 129, 0.1" : 
                colorBase === "orange" ? "249, 115, 22, 0.1" : 
                colorBase === "purple" ? "139, 92, 246, 0.1" : 
                "2, 132, 199, 0.1" // default to primary-600
              })`,
              color: `${
                colorBase === "blue" ? "#3b82f6" : 
                colorBase === "green" ? "#10b981" : 
                colorBase === "orange" ? "#f97316" : 
                colorBase === "purple" ? "#8b5cf6" : 
                "#0284c7" // default to primary-600
              }`
            }}
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Selected
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeBaseCard; 