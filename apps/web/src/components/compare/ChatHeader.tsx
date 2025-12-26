/**
 * BLOCK 0: ChatHeader
 * Displays user query (original + normalized)
 *
 * Constitution: Fact-only display, no interpretation
 */

import React from "react";
import type { Header } from "@/lib/compare/viewModelTypes";

interface ChatHeaderProps {
  header: Header;
}

export function ChatHeader({ header }: ChatHeaderProps) {
  return (
    <div className="mb-6 border-b pb-4">
      <div className="text-lg font-medium text-gray-900">
        {header.user_query}
      </div>
      {header.normalized_query && (
        <div className="mt-1 text-sm text-gray-500">
          {header.normalized_query}
        </div>
      )}
    </div>
  );
}
