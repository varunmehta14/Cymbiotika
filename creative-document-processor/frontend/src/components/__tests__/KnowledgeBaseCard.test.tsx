import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import KnowledgeBaseCard from "../KnowledgeBaseCard";
import { Folder } from "lucide-react";

describe("KnowledgeBaseCard", () => {
  const mockKb = {
    id: "test-kb",
    name: "Test KB",
    description: "Test description",
    icon: <Folder data-testid="folder-icon" />,
  };
  
  const mockOnSelect = jest.fn();
  
  beforeEach(() => {
    mockOnSelect.mockClear();
  });
  
  test("renders correctly with provided props", () => {
    render(
      <KnowledgeBaseCard
        kb={mockKb}
        selected={false}
        onSelect={mockOnSelect}
      />
    );
    
    // Check that name and description are rendered
    expect(screen.getByText("Test KB")).toBeInTheDocument();
    expect(screen.getByText("Test description")).toBeInTheDocument();
    
    // Check that icon is rendered
    expect(screen.getByTestId("folder-icon")).toBeInTheDocument();
  });
  
  test("applies selected styles when selected prop is true", () => {
    const { container, rerender } = render(
      <KnowledgeBaseCard
        kb={mockKb}
        selected={false}
        onSelect={mockOnSelect}
      />
    );
    
    // Check initial state (not selected)
    const card = container.firstChild as HTMLElement;
    expect(card).not.toHaveClass("border-primary-500");
    expect(card).not.toHaveClass("bg-primary-50");
    
    // Rerender with selected=true
    rerender(
      <KnowledgeBaseCard
        kb={mockKb}
        selected={true}
        onSelect={mockOnSelect}
      />
    );
    
    // Check that selected styles are applied
    expect(card).toHaveClass("border-primary-500");
    expect(card).toHaveClass("bg-primary-50");
  });
  
  test("calls onSelect when clicked", () => {
    render(
      <KnowledgeBaseCard
        kb={mockKb}
        selected={false}
        onSelect={mockOnSelect}
      />
    );
    
    // Find the card and click it
    const card = screen.getByText("Test KB").closest("div");
    fireEvent.click(card as HTMLElement);
    
    // Check that onSelect was called
    expect(mockOnSelect).toHaveBeenCalledTimes(1);
  });
}); 