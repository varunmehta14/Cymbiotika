"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileText, Upload, RefreshCw, Database, Book, FileCode, Beaker, Sparkles } from "lucide-react";

import KnowledgeBaseCard from "@/components/KnowledgeBaseCard";
import DocumentUploader from "@/components/DocumentUploader";

type KnowledgeBase = {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
};

export default function Home() {
  const router = useRouter();
  const [selectedKb, setSelectedKb] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Define available knowledge bases
  const knowledgeBases: KnowledgeBase[] = [
    {
      id: "resumes",
      name: "Resumes",
      description: "Match job descriptions to candidate resumes",
      icon: <FileText className="h-5 w-5" />,
      color: "from-blue-500 to-cyan-500"
    },
    {
      id: "api_docs",
      name: "API Documentation",
      description: "Query and understand API documentation",
      icon: <FileCode className="h-5 w-5" />,
      color: "from-green-500 to-emerald-500"
    },
    {
      id: "recipes",
      name: "Recipes",
      description: "Enhance and improve cooking recipes",
      icon: <Book className="h-5 w-5" />,
      color: "from-orange-500 to-amber-500"
    },
    {
      id: "supplements",
      name: "Supplements",
      description: "Get personalized wellness recommendations",
      icon: <Beaker className="h-5 w-5" />,
      color: "from-purple-500 to-violet-500"
    }
  ];
  
  // Handle document upload success
  const handleUploadSuccess = (documentId: string, kb: string) => {
    router.push(`/kb/${kb}`);
  };
  
  // Handle refresh products
  const handleRefreshProducts = async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/scrape/refresh_products`, {
        method: "POST",
      });
      
      if (!response.ok) {
        throw new Error("Failed to refresh products");
      }
      
      // Wait 3 seconds to simulate loading
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Redirect to supplements KB
      router.push("/kb/supplements");
    } catch (error) {
      console.error("Error refreshing products:", error);
    } finally {
      setIsRefreshing(false);
    }
  };
  
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome header */}
      <div className="text-center mb-14 relative">
        {/* Background effects */}
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-64 h-64 bg-gradient-to-r from-primary-300/20 to-secondary-300/20 rounded-full blur-3xl -z-10"></div>
        <div className="absolute top-10 left-1/4 w-16 h-16 bg-blue-400/10 rounded-full blur-2xl animate-pulse-slow"></div>
        <div className="absolute top-20 right-1/4 w-20 h-20 bg-purple-400/10 rounded-full blur-2xl animate-pulse-slow" style={{ animationDelay: "1s" }}></div>
        
        {/* Header content */}
        <div className="relative">
          <Sparkles className="h-10 w-10 absolute -top-6 -left-6 text-yellow-400 animate-bounce-slow" />
          <h1 className="text-4xl font-bold mb-4 inline-flex items-center relative">
            <span className="gradient-text">AI-Powered Document Processing</span>
            <Sparkles className="h-6 w-6 ml-2 text-yellow-400 animate-pulse-slow" />
          </h1>
        </div>
        <p className="text-slate-600 max-w-2xl mx-auto text-lg">
          Upload documents to specialized knowledge bases and interact with them using natural language queries powered by Google Gemini.
        </p>
      </div>
      
      {/* Knowledge Base Selection */}
      <div className="card p-8 animate-slide-in-bottom" style={{ animationDelay: "100ms" }}>
        <h2 className="text-xl font-semibold mb-6 flex items-center">
          <Database className="h-5 w-5 mr-2 text-primary-500" />
          Select a Knowledge Base
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {knowledgeBases.map((kb, index) => (
            <KnowledgeBaseCard
              key={kb.id}
              kb={kb}
              selected={selectedKb === kb.id}
              onSelect={() => setSelectedKb(kb.id)}
              colorGradient={kb.color}
              animationDelay={index * 150}
            />
          ))}
        </div>
      </div>
      
      {/* Upload Document Section - Only shown if a KB is selected */}
      {selectedKb && (
        <div className="card p-8 animate-slide-in-bottom" style={{ animationDelay: "300ms" }}>
          <h2 className="text-xl font-semibold mb-6 flex items-center">
            <Upload className="h-5 w-5 mr-2 text-primary-500" />
            Upload Document or Add URL
          </h2>
          
          <DocumentUploader 
            kb={selectedKb} 
            onSuccess={handleUploadSuccess} 
          />
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4 animate-slide-in-bottom" style={{ animationDelay: "400ms" }}>
        <Link
          href={`/kb/${selectedKb || "resumes"}`}
          className={`btn px-5 py-3 rounded-lg ${!selectedKb 
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
            : 'btn-primary'}`}
          style={{ pointerEvents: selectedKb ? "auto" : "none" }}
        >
          <Database className="h-4 w-4 mr-2" />
          Browse {selectedKb ? knowledgeBases.find(kb => kb.id === selectedKb)?.name : ""} Database
        </Link>
        
        {selectedKb === "supplements" && (
          <button
            onClick={handleRefreshProducts}
            disabled={isRefreshing}
            className="btn btn-secondary px-5 py-3 rounded-lg"
          >
            {isRefreshing ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Refreshing Products...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Products
              </>
            )}
          </button>
        )}
      </div>
      
      {/* Help Card */}
      <div className="card p-8 border-l-4 border-l-primary-500 mt-8 animate-slide-in-bottom glass-effect" style={{ animationDelay: "500ms" }}>
        <h3 className="text-lg font-semibold mb-3 gradient-text">Getting Started</h3>
        <ol className="list-decimal list-inside text-slate-700 space-y-3 ml-2">
          <li className="animate-slide-in-bottom" style={{ animationDelay: "600ms" }}>
            Select a knowledge base from the options above
          </li>
          <li className="animate-slide-in-bottom" style={{ animationDelay: "700ms" }}>
            Upload a document or provide a URL to add content
          </li>
          <li className="animate-slide-in-bottom" style={{ animationDelay: "800ms" }}>
            Browse the database to view your documents
          </li>
          <li className="animate-slide-in-bottom" style={{ animationDelay: "900ms" }}>
            Ask questions about your documents using natural language
          </li>
        </ol>
      </div>
    </div>
  );
} 