"use client";

import React, { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { Loader } from "lucide-react";

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

type DocumentPreviewProps = {
  kb: string;
  documentId: string;
};

const DocumentPreview: React.FC<DocumentPreviewProps> = ({ kb, documentId }) => {
  const [content, setContent] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);

  useEffect(() => {
    async function fetchDocument() {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/doc/${kb}/${documentId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch document: ${response.statusText}`);
        }
        
        // Get content type from headers
        const contentTypeHeader = response.headers.get("content-type");
        setContentType(contentTypeHeader);
        
        if (contentTypeHeader?.includes("application/pdf")) {
          // For PDFs, we get blob to pass to PDF viewer
          const blob = await response.blob();
          setContent(URL.createObjectURL(blob));
        } else {
          // For text content, we get the text
          const text = await response.text();
          setContent(text);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred");
        console.error("Error fetching document:", err);
      } finally {
        setIsLoading(false);
      }
    }
    
    if (kb && documentId) {
      fetchDocument();
    }
    
    // Cleanup function to revoke object URLs
    return () => {
      if (content && contentType?.includes("application/pdf")) {
        URL.revokeObjectURL(content);
      }
    };
  }, [kb, documentId]);
  
  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 text-red-500 text-center">
        <p>Error loading document:</p>
        <p className="font-medium">{error}</p>
      </div>
    );
  }
  
  if (!content) {
    return (
      <div className="p-4 text-gray-500 text-center">
        <p>No document content available</p>
      </div>
    );
  }
  
  // Render PDF
  if (contentType?.includes("application/pdf")) {
    return (
      <div className="p-4 overflow-auto h-full flex flex-col items-center">
        <Document
          file={content}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="flex justify-center items-center h-20">
              <Loader className="w-5 h-5 animate-spin text-primary-500" />
            </div>
          }
          error={
            <div className="p-4 text-red-500 text-center">
              <p>Error loading PDF document</p>
            </div>
          }
        >
          {Array.from(new Array(numPages), (_, index) => (
            <Page 
              key={`page_${index + 1}`}
              pageNumber={index + 1} 
              width={600}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          ))}
        </Document>
      </div>
    );
  }
  
  // Render text content
  return (
    <div className="p-4 overflow-auto h-full">
      <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800">{content}</pre>
    </div>
  );
};

export default DocumentPreview; 