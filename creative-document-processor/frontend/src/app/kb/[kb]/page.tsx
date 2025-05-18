"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Folder, FileText, RefreshCw } from "lucide-react";

import DocumentList from "@/components/DocumentList";
import DocumentPreview from "@/components/DocumentPreview";
import ChatInterface from "@/components/ChatInterface";

export default function KnowledgeBasePage() {
  const params = useParams();
  const kb = params.kb as string;
  
  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch documents for the current KB
  useEffect(() => {
    async function fetchDocuments() {
      try {
        setIsLoading(true);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/doc/${kb}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch documents: ${response.statusText}`);
        }
        
        const data = await response.json();
        setDocuments(data);
        
        // Select the first document if available
        if (data.length > 0 && !selectedDocId) {
          setSelectedDocId(data[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred");
        console.error("Error fetching documents:", err);
      } finally {
        setIsLoading(false);
      }
    }
    
    fetchDocuments();
  }, [kb, selectedDocId]);
  
  // Get the title of the current KB
  const getKbTitle = () => {
    switch (kb) {
      case "resumes":
        return "Resumes";
      case "api_docs":
        return "API Documentation";
      case "recipes":
        return "Recipes";
      case "supplements":
        return "Supplements";
      default:
        return "Knowledge Base";
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">
          <Folder className="h-6 w-6 inline-block mr-2 text-primary-500" />
          {getKbTitle()}
        </h1>
        
        <button
          onClick={() => window.location.reload()}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </button>
      </div>
      
      <div className="flex h-[calc(100vh-220px)] space-x-4 overflow-hidden">
        {/* Left panel: Document list */}
        <div className="w-1/4 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          <div className="p-4 bg-gray-50 border-b">
            <h2 className="text-lg font-medium text-gray-900">Documents</h2>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {isLoading ? (
              <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
              </div>
            ) : error ? (
              <div className="text-red-500 text-center">
                {error}
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <FileText className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                <p>No documents in this knowledge base yet.</p>
                <p className="text-sm mt-2">
                  Upload documents from the home page to get started.
                </p>
              </div>
            ) : (
              <DocumentList
                documents={documents}
                selectedId={selectedDocId}
                onSelect={setSelectedDocId}
              />
            )}
          </div>
        </div>
        
        {/* Right panel: Document preview and chat */}
        <div className="w-3/4 flex flex-col space-y-4">
          {/* Document preview */}
          {selectedDocId && (
            <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
              <DocumentPreview kb={kb} documentId={selectedDocId} />
            </div>
          )}
          
          {/* Chat interface */}
          <div className="h-1/2 bg-white rounded-lg shadow overflow-hidden">
            <ChatInterface kb={kb} documentId={selectedDocId} />
          </div>
        </div>
      </div>
    </div>
  );
} 