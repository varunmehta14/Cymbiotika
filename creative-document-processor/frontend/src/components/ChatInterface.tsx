"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Loader, MessageSquare, PenSquare } from "lucide-react";
import ReactMarkdown from "react-markdown";

type ChatMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

type ChatInterfaceProps = {
  kb: string;
  documentId: string | null;
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ kb, documentId }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreamingResponse, setIsStreamingResponse] = useState(false);
  const [currentStreamedMessage, setCurrentStreamedMessage] = useState("");
  const [toneForRewrite, setToneForRewrite] = useState("professional");
  const [isRewriteMode, setIsRewriteMode] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentStreamedMessage]);
  
  // Get title for the chat based on KB type
  const getChatTitle = () => {
    switch (kb) {
      case "resumes":
        return "Job Matching Assistant";
      case "api_docs":
        return "API Documentation Assistant";
      case "recipes":
        return "Recipe Enhancement Assistant";
      case "supplements":
        return "Wellness Advisor";
      default:
        return "AI Assistant";
    }
  };
  
  // Get placeholder for the chat input based on KB type
  const getInputPlaceholder = () => {
    switch (kb) {
      case "resumes":
        return "Enter job description to match...";
      case "api_docs":
        return "Ask about API endpoints, parameters, etc...";
      case "recipes":
        return "Ask to enhance this recipe or for alternatives...";
      case "supplements":
        return "Ask for wellness recommendations or product info...";
      default:
        return "Type your message...";
    }
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;
    
    // Add user message
    const userMessage: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    
    // Clear input field
    setInput("");
    
    // Focus input field after submission
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    
    setIsLoading(true);
    setIsStreamingResponse(true);
    setCurrentStreamedMessage("");
    
    try {
      let endpoint: string;
      let body: any;
      
      if (isRewriteMode && kb === "supplements" && documentId) {
        // Supplement rewrite mode
        endpoint = `${process.env.NEXT_PUBLIC_API_URL}/query/supplement/rewrite`;
        body = {
          doc_id: documentId,
          tone: toneForRewrite
        };
      } else {
        // Normal query mode
        endpoint = `${process.env.NEXT_PUBLIC_API_URL}/query`;
        body = {
          kb,
          prompt: input,
          doc_id: documentId
        };
      }
      
      // Create a POST request to get the SSE stream
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${await response.text()}`);
      }
      
      // Set up a reader to process the streaming response
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }
      
      // Read the stream
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        console.log("Received chunk:", chunk); // For debugging
        
        // Process SSE data - split by "data:" prefix and process each event
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data:')) {
            const eventData = line.substring(5).trim();
            console.log("Event data:", eventData); // For debugging
            
            try {
              const data = JSON.parse(eventData);
              
              if (typeof data === "string") {
                // Text message
                setCurrentStreamedMessage((prev) => prev + data);
              } else if (typeof data === "object") {
                // Status message
                if (data.status === "complete") {
                  const finalMessage = data.answer || data.rewritten || "No response received";
                  
                  // Add assistant message
                  const assistantMessage: ChatMessage = {
                    role: "assistant",
                    content: finalMessage
                  };
                  
                  setMessages((prev) => [...prev, assistantMessage]);
                  setCurrentStreamedMessage("");
                  setIsStreamingResponse(false);
                  break;
                } else if (data.status === "error") {
                  // Handle error
                  setCurrentStreamedMessage(`Error: ${data.message || "Unknown error"}`);
                  setIsStreamingResponse(false);
                  break;
                }
              } else {
                setCurrentStreamedMessage((prev) => prev + eventData);
              }
            } catch (error) {
              // If not JSON, just add the text
              console.log("Error parsing JSON:", error); // For debugging
              setCurrentStreamedMessage((prev) => prev + eventData);
            }
          }
        }
      }
      
      // If we still have streamed content at the end, add it as a message
      if (isStreamingResponse && currentStreamedMessage) {
        const assistantMessage: ChatMessage = {
          role: "assistant", 
          content: currentStreamedMessage
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setCurrentStreamedMessage("");
        setIsStreamingResponse(false);
      }
    } catch (error) {
      console.error("Error calling API:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
        },
      ]);
      setIsStreamingResponse(false);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };
  
  // Handle key press (Enter to send)
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="border-b px-4 py-2 flex justify-between items-center">
        <h2 className="font-medium text-gray-900">
          <MessageSquare className="h-4 w-4 inline-block mr-2 text-primary-500" />
          {getChatTitle()}
        </h2>
        
        {kb === "supplements" && documentId && (
          <button
            onClick={() => setIsRewriteMode(!isRewriteMode)}
            className={`px-2 py-1 text-xs rounded-md ${
              isRewriteMode ? "bg-secondary-100 text-secondary-800" : "bg-gray-100 text-gray-800"
            }`}
          >
            <PenSquare className="h-3 w-3 inline-block mr-1" />
            {isRewriteMode ? "Cancel Rewrite" : "Rewrite Mode"}
          </button>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isStreamingResponse ? (
          <div className="text-center text-gray-500 my-8">
            <MessageSquare className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>No messages yet</p>
            <p className="text-sm mt-1">
              {documentId 
                ? "Ask a question about this document"
                : "Select a document to ask questions about it or just start chatting"}
            </p>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${
                  message.role === "user"
                    ? "bg-primary-50 ml-8"
                    : message.role === "system"
                    ? "bg-red-50 text-red-800"
                    : "bg-gray-100 mr-8"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="text-sm markdown-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
            ))}
            
            {isStreamingResponse && currentStreamedMessage && (
              <div className="p-3 rounded-lg bg-gray-100 mr-8">
                <div className="text-sm markdown-content">
                  <ReactMarkdown>{currentStreamedMessage}</ReactMarkdown>
                </div>
              </div>
            )}
          </>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {isRewriteMode && kb === "supplements" && (
        <div className="px-4 py-2 bg-secondary-50 border-t">
          <div className="flex items-center">
            <label htmlFor="tone-selector" className="text-sm font-medium text-gray-700 mr-2">
              Tone:
            </label>
            <select
              id="tone-selector"
              value={toneForRewrite}
              onChange={(e) => setToneForRewrite(e.target.value)}
              className="text-sm rounded-md border-gray-300 shadow-sm focus:border-secondary-500 focus:ring-secondary-500"
            >
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="enthusiastic">Enthusiastic</option>
              <option value="scientific">Scientific</option>
              <option value="persuasive">Persuasive</option>
            </select>
            <p className="text-xs text-gray-500 ml-2">Rewrite product description with selected tone</p>
          </div>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="border-t p-2 flex items-end">
        <textarea
          ref={inputRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          placeholder={getInputPlaceholder()}
          rows={1}
          className="flex-1 border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="ml-2 p-2 rounded-md bg-primary-500 text-white disabled:opacity-50"
        >
          {isLoading ? (
            <Loader className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface; 