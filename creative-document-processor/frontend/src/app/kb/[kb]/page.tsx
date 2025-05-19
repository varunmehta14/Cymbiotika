"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Folder, FileText, RefreshCw } from "lucide-react";

import DocumentList from "@/components/DocumentList";
import DocumentPreview from "@/components/DocumentPreview";
import ChatInterface from "@/components/ChatInterface";
import ReactMarkdown from 'react-markdown';

export default function KnowledgeBasePage() {
  const params = useParams();
  const kb = params.kb as string;
  
  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Add tab state
  const [activeTab, setActiveTab] = useState<'chat' | 'compare'>('chat');

  // Resume comparison state
  const [jobDescription, setJobDescription] = useState('');
  const [selectedResumes, setSelectedResumes] = useState<string[]>([]);
  const [isComparing, setIsComparing] = useState(false);
  const [progressStatus, setProgressStatus] = useState('');
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [result, setResult] = useState<string | null>(null);
  const [selectAll, setSelectAll] = useState(false);
  const [toastMessage, setToastMessage] = useState<{title: string, message: string, type: 'success'|'error'|'warning'|'info'} | null>(null);
  
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

  // Auto-hide toast after 3 seconds
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => {
        setToastMessage(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Handle selecting all resumes
  useEffect(() => {
    if (kb === 'resumes') {
      if (selectAll) {
        setSelectedResumes(documents.map(resume => resume.id));
      } else if (selectedResumes.length === documents.length) {
        // If all were selected and selectAll is now false, clear selection
        setSelectedResumes([]);
      }
    }
  }, [selectAll, documents, kb]);
  
  // Handle resume selection
  const handleResumeSelection = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSelectedResumes(prev => {
      if (prev.includes(value)) {
        return prev.filter(id => id !== value);
      } else {
        return [...prev, value];
      }
    });
  };

  // Handle comparison
  const handleCompare = async () => {
    if (!jobDescription.trim()) {
      setToastMessage({
        title: 'Job description required',
        message: 'Please enter a job description to compare resumes against',
        type: 'warning'
      });
      return;
    }

    // Use all resumes if none selected
    const resumeIds = selectedResumes.length > 0 ? selectedResumes : null;

    setIsComparing(true);
    setProgressStatus('Starting comparison...');
    setProgressPercentage(10);
    setResult(null);

    try {
      // Set up SSE connection
      const eventSource = new EventSource(
        `${process.env.NEXT_PUBLIC_API_URL}/documents/compare-resumes?_=${Date.now()}`
      );

      // Send the request data
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents/compare-resumes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_description: jobDescription,
          document_ids: resumeIds,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start comparison');
      }

      // Handle SSE events
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Update progress
        if (data.message) {
          setProgressStatus(data.message);
          // Increment progress (approximate)
          setProgressPercentage(prev => Math.min(prev + 10, 90));
        }
        
        // Handle final result
        if (event.type === 'result' && data.result) {
          setResult(data.result.final_answer);
          setProgressPercentage(100);
          setProgressStatus('Comparison complete!');
          eventSource.close();
          setIsComparing(false);
        }
      };

      // Handle errors
      eventSource.onerror = () => {
        eventSource.close();
        setIsComparing(false);
        setToastMessage({
          title: 'Error during comparison',
          message: 'There was an error during the resume comparison process',
          type: 'error'
        });
      };
    } catch (error) {
      setIsComparing(false);
      setToastMessage({
        title: 'Error starting comparison',
        message: error instanceof Error ? error.message : 'Unknown error',
        type: 'error'
      });
    }
  };
  
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
  
  // Resume comparison component
  const ResumeComparisonSection = () => (
    <div className="h-full p-4">
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Resume Comparison</h3>
        <p className="text-sm text-gray-600">
          Enter a job description below and select resumes to compare. The system will analyze and rank the best candidates for the position.
        </p>

        {/* Toast message */}
        {toastMessage && (
          <div className={`p-3 rounded-md mb-4 ${
            toastMessage.type === 'error' ? 'bg-red-100 text-red-800' : 
            toastMessage.type === 'warning' ? 'bg-yellow-100 text-yellow-800' : 
            toastMessage.type === 'success' ? 'bg-green-100 text-green-800' : 
            'bg-blue-100 text-blue-800'
          }`}>
            <h4 className="font-medium">{toastMessage.title}</h4>
            <p className="text-sm">{toastMessage.message}</p>
          </div>
        )}

        {/* Job Description Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="job-description">
            Job Description <span className="text-red-500">*</span>
          </label>
          <textarea
            id="job-description"
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
            rows={4}
            disabled={isComparing}
          />
        </div>

        {/* Resume Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select Resumes to Compare
          </label>
          <div className="mb-2">
            <label className="inline-flex items-center">
              <input
                type="checkbox"
                checked={selectAll}
                onChange={(e) => setSelectAll(e.target.checked)}
                className="form-checkbox h-4 w-4 text-primary-600 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Select All ({documents.length})</span>
            </label>
          </div>
          
          <div className="border rounded-md p-3 max-h-36 overflow-y-auto">
            <div className="space-y-2">
              {documents.map(resume => (
                <label key={resume.id} className="flex items-center">
                  <input
                    type="checkbox"
                    value={resume.id}
                    checked={selectedResumes.includes(resume.id)}
                    onChange={handleResumeSelection}
                    className="form-checkbox h-4 w-4 text-primary-600 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">{resume.name || resume.filename}</span>
                </label>
              ))}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Leave all unselected to compare against all available resumes
          </p>
        </div>

        {/* Compare Button */}
        <button
          onClick={handleCompare}
          disabled={isComparing}
          className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 flex items-center"
        >
          {isComparing ? (
            <>
              <span className="mr-2 animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
              Comparing...
            </>
          ) : "Compare Resumes"}
        </button>

        {/* Progress Indicator */}
        {isComparing && (
          <div className="mt-4">
            <p className="text-sm text-gray-700 mb-1">{progressStatus}</p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-500 h-2 rounded-full"
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="mt-4 border rounded-md overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b">
              <h4 className="text-sm font-medium">Comparison Results</h4>
            </div>
            <div className="p-4">
              <div className="markdown-content">
                <ReactMarkdown>{result}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Link href="/" className="flex items-center hover:opacity-80 transition-opacity">
          <h1 className="text-2xl font-bold text-gray-900">
            <Folder className="h-6 w-6 inline-block mr-2 text-primary-500" />
            {getKbTitle()}
          </h1>
        </Link>
        
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
        
        {/* Right panel: Document preview and features */}
        <div className="w-3/4 flex flex-col space-y-4">
          {/* Document preview - adjust height to be smaller */}
          {selectedDocId && (
            <div className="h-[40%] bg-white rounded-lg shadow overflow-hidden">
              <DocumentPreview kb={kb} documentId={selectedDocId} />
            </div>
          )}
          
          {/* Features section - increase height */}
          {kb === "resumes" ? (
            <div className="h-[60%] bg-white rounded-lg shadow overflow-hidden flex flex-col">
              {/* Tabs */}
              <div className="flex border-b">
                <button
                  className={`px-4 py-2 text-sm font-medium ${
                    activeTab === 'chat'
                      ? 'border-b-2 border-primary-500 text-primary-600'
                      : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                  onClick={() => setActiveTab('chat')}
                >
                  Chat
                </button>
                <button
                  className={`px-4 py-2 text-sm font-medium ${
                    activeTab === 'compare'
                      ? 'border-b-2 border-primary-500 text-primary-600'
                      : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                  onClick={() => setActiveTab('compare')}
                >
                  Compare Resumes
                </button>
              </div>
              
              {/* Tab content - make sure to fill available height */}
              <div className="flex-1 h-full overflow-auto">
                {activeTab === 'chat' ? (
                  <div className="h-full">
                    <ChatInterface kb={kb} documentId={selectedDocId} />
                  </div>
                ) : (
                  <div className="h-full">
                    <ResumeComparisonSection />
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-[60%] bg-white rounded-lg shadow overflow-hidden">
              <ChatInterface kb={kb} documentId={selectedDocId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 