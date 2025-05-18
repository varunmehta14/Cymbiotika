"use client";

import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Link as LinkIcon, Loader, FileType } from "lucide-react";

type DocumentUploaderProps = {
  kb: string;
  onSuccess: (documentId: string, kb: string) => void;
};

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ kb, onSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [uploadMethod, setUploadMethod] = useState<"file" | "url">("file");

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      setIsUploading(true);
      setError(null);

      const file = acceptedFiles[0];
      const formData = new FormData();
      formData.append("file", file);
      formData.append("kb", kb);

      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ingest`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to upload document");
        }

        const data = await response.json();
        onSuccess(data.id, kb);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error occurred");
      } finally {
        setIsUploading(false);
      }
    },
    [kb, onSuccess]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
    },
    disabled: isUploading || uploadMethod !== "file",
    maxFiles: 1,
  });

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("url", urlInput);
    formData.append("kb", kb);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ingest`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to ingest from URL");
      }

      const data = await response.json();
      onSuccess(data.id, kb);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex space-x-4 border-b border-slate-200/50 pb-4">
        <button
          type="button"
          className={`px-5 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
            uploadMethod === "file"
              ? "bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md shadow-primary-500/20"
              : "bg-white/80 text-slate-700 hover:bg-slate-100 hover:scale-105"
          }`}
          onClick={() => setUploadMethod("file")}
        >
          <Upload className="h-4 w-4 inline mr-2" />
          Upload File
        </button>
        <button
          type="button"
          className={`px-5 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
            uploadMethod === "url"
              ? "bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md shadow-primary-500/20"
              : "bg-white/80 text-slate-700 hover:bg-slate-100 hover:scale-105"
          }`}
          onClick={() => setUploadMethod("url")}
        >
          <LinkIcon className="h-4 w-4 inline mr-2" />
          Add URL
        </button>
      </div>

      {uploadMethod === "file" ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
            isDragActive
              ? "border-primary-500 bg-primary-50/50 backdrop-blur-sm transform scale-[1.02]"
              : "border-slate-300/70 hover:border-primary-400 hover:bg-white/50 backdrop-blur-sm"
          } ${isUploading ? "opacity-70 cursor-not-allowed" : ""}`}
        >
          <input {...getInputProps()} />
          <div className="mb-4">
            {isDragActive ? (
              <div className="bg-primary-100 text-primary-600 rounded-full p-3 w-14 h-14 mx-auto flex items-center justify-center animate-pulse">
                <Upload className="h-6 w-6" />
              </div>
            ) : (
              <div className="bg-slate-100 rounded-full p-3 w-14 h-14 mx-auto flex items-center justify-center text-slate-500">
                <FileType className="h-6 w-6" />
              </div>
            )}
          </div>
          
          {isDragActive ? (
            <p className="text-primary-600 font-medium">Drop the file here...</p>
          ) : (
            <>
              <p className="text-slate-700 font-medium mb-2">
                Drag & drop a file here, or click to select
              </p>
              <p className="text-sm text-slate-500 mt-1">
                Supported formats: PDF, TXT, MD
              </p>
            </>
          )}
          {isUploading && (
            <div className="mt-4 glass-effect p-3 rounded-lg inline-block mx-auto">
              <Loader className="h-5 w-5 animate-spin mx-auto text-primary-500" />
              <p className="text-sm text-primary-700 mt-1">Processing document...</p>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleUrlSubmit} className="space-y-4 animate-slide-in-bottom">
          <div>
            <label
              htmlFor="url-input"
              className="block text-sm font-medium text-slate-700 mb-2"
            >
              Enter Document URL
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <LinkIcon className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="url"
                name="url"
                id="url-input"
                className="pl-10 flex-1 min-w-0 block w-full px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white/80 backdrop-blur-sm transition-all duration-200"
                placeholder="https://example.com/document.pdf"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                disabled={isUploading}
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={isUploading || !urlInput.trim()}
            className="inline-flex items-center px-5 py-2.5 border border-transparent text-sm font-medium rounded-lg shadow-md shadow-primary-500/20 text-white bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-700 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 transition-all duration-200 hover:shadow-lg hover:shadow-primary-500/30 transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {isUploading ? (
              <>
                <Loader className="h-4 w-4 animate-spin mr-2" />
                Processing...
              </>
            ) : (
              <>
                <LinkIcon className="h-4 w-4 mr-2" />
                Process URL
              </>
            )}
          </button>
        </form>
      )}

      {error && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg animate-fade-in">
          <p className="text-sm font-medium flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            {error}
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentUploader; 