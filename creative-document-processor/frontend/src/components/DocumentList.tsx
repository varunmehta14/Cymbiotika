"use client";

import React from "react";
import { FileText, Link as LinkIcon } from "lucide-react";
import clsx from "clsx";

type Document = {
  id: string;
  title: string;
  source: string;
  source_type: "file" | "url";
  created_at: string;
  content_type: string;
  chunk_count: number;
};

type DocumentListProps = {
  documents: Document[];
  selectedId: string | null;
  onSelect: (documentId: string) => void;
};

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedId,
  onSelect,
}) => {
  // Format the date string
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date);
  };

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className={clsx(
            "p-3 rounded-md cursor-pointer transition-colors",
            {
              "bg-primary-50 border-l-4 border-primary-500": selectedId === doc.id,
              "hover:bg-gray-50 border-l-4 border-transparent": selectedId !== doc.id,
            }
          )}
          onClick={() => onSelect(doc.id)}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-1">
              {doc.source_type === "url" ? (
                <LinkIcon className="h-5 w-5 text-gray-400" />
              ) : (
                <FileText className="h-5 w-5 text-gray-400" />
              )}
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900 line-clamp-1">
                {doc.title}
              </p>
              <p className="text-xs text-gray-500 truncate mt-0.5">
                {doc.source_type === "url" ? "URL: " : "File: "}
                {doc.source}
              </p>
              <div className="flex justify-between mt-1 text-xs text-gray-500">
                <span>{formatDate(doc.created_at)}</span>
                <span>{doc.chunk_count} chunks</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DocumentList; 