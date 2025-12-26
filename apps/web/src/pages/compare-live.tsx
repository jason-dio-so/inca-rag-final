/**
 * Compare Live - ChatGPT Style UI with Real API
 * Purpose: E2E validation of API → ViewModel → UI rendering
 *
 * Flow:
 * 1. User enters query in chat input (left panel)
 * 2. Submit → POST /compare/view-model
 * 3. Receive ViewModel v2
 * 4. Render with CompareViewModelRenderer
 * 5. Evidence panel interaction (click → scroll/highlight)
 *
 * Constitutional Compliance:
 * - Fact-only rendering
 * - NO recommendation/judgment/interpretation
 * - Evidence-based display
 */

import React, { useState } from "react";
import { CompareViewModelRenderer } from "@/components/compare/CompareViewModelRenderer";
import type { CompareViewModel } from "@/lib/compare/viewModelTypes";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  viewModel?: CompareViewModel;
}

export default function CompareLivePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: "user",
      content: inputQuery.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8001/compare/view-model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMessage.content,
          // Optional: extract insurers from query or use all
          insurers: ["SAMSUNG", "MERITZ", "HANWHA"],
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const viewModel: CompareViewModel = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: "assistant",
        content: "비교 결과",
        viewModel,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "네트워크 오류");

      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: "assistant",
        content: `오류 발생: ${err instanceof Error ? err.message : "알 수 없는 오류"}`,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery: string) => {
    setInputQuery(exampleQuery);
  };

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white px-6 py-4 shadow-sm">
        <h1 className="text-xl font-semibold text-gray-900">
          보험 비교 (ChatGPT Style - Live API)
        </h1>
        <p className="text-sm text-gray-600">
          실제 /compare API 호출 → ViewModel v2 → UI 렌더링
        </p>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Chat Messages */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center text-gray-500">
                <div className="mb-4 text-center">
                  <div className="text-lg font-medium">질문을 입력하세요</div>
                  <div className="mt-2 text-sm">
                    예시를 클릭하면 자동으로 입력됩니다
                  </div>
                </div>

                {/* Example Queries */}
                <div className="mt-6 grid max-w-2xl grid-cols-1 gap-3 md:grid-cols-2">
                  <button
                    onClick={() =>
                      handleExampleClick(
                        "가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
                      )
                    }
                    className="rounded-lg border border-gray-200 bg-white p-4 text-left text-sm hover:bg-gray-50"
                  >
                    <div className="font-medium text-gray-900">Example 1</div>
                    <div className="mt-1 text-gray-600">
                      보험료 정렬순으로 비교
                    </div>
                  </button>

                  <button
                    onClick={() =>
                      handleExampleClick(
                        "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
                      )
                    }
                    className="rounded-lg border border-gray-200 bg-white p-4 text-left text-sm hover:bg-gray-50"
                  >
                    <div className="font-medium text-gray-900">Example 2</div>
                    <div className="mt-1 text-gray-600">
                      보장한도 차이 감지
                    </div>
                  </button>

                  <button
                    onClick={() =>
                      handleExampleClick(
                        "삼성화재, 메리츠화재의 암진단비를 비교해줘"
                      )
                    }
                    className="rounded-lg border border-gray-200 bg-white p-4 text-left text-sm hover:bg-gray-50"
                  >
                    <div className="font-medium text-gray-900">Example 3</div>
                    <div className="mt-1 text-gray-600">
                      특정 보험사 비교
                    </div>
                  </button>

                  <button
                    onClick={() =>
                      handleExampleClick(
                        "제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 상품 비교해줘"
                      )
                    }
                    className="rounded-lg border border-gray-200 bg-white p-4 text-left text-sm hover:bg-gray-50"
                  >
                    <div className="font-medium text-gray-900">Example 4</div>
                    <div className="mt-1 text-gray-600">
                      질병별 O/X 매트릭스
                    </div>
                  </button>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`mb-6 ${
                  message.type === "user" ? "text-right" : "text-left"
                }`}
              >
                {message.type === "user" ? (
                  <div className="inline-block max-w-3xl rounded-lg bg-blue-600 px-4 py-2 text-white">
                    {message.content}
                  </div>
                ) : (
                  <div className="max-w-full">
                    {message.viewModel ? (
                      <div className="rounded-lg bg-white p-6 shadow-md">
                        <CompareViewModelRenderer viewModel={message.viewModel} />
                      </div>
                    ) : (
                      <div className="inline-block rounded-lg bg-gray-200 px-4 py-2 text-gray-900">
                        {message.content}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="mb-6 text-left">
                <div className="inline-block rounded-lg bg-gray-200 px-4 py-2 text-gray-900">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 animate-pulse rounded-full bg-gray-500"></div>
                    <div className="h-2 w-2 animate-pulse rounded-full bg-gray-500" style={{ animationDelay: "0.2s" }}></div>
                    <div className="h-2 w-2 animate-pulse rounded-full bg-gray-500" style={{ animationDelay: "0.4s" }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t bg-white px-6 py-4">
            {error && (
              <div className="mb-3 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="보험 비교 질문을 입력하세요..."
                disabled={isLoading}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
              />
              <button
                type="submit"
                disabled={isLoading || !inputQuery.trim()}
                className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300"
              >
                {isLoading ? "처리중..." : "전송"}
              </button>
            </form>

            <div className="mt-2 text-xs text-gray-500">
              ※ Constitutional: 추천/우열/해석/추론 문구 생성 금지 (Fact-only)
            </div>
          </div>
        </div>

        {/* Right: Info Panel (Optional - for future Evidence interaction) */}
        <div className="hidden lg:block w-80 border-l bg-white p-6">
          <h3 className="mb-4 text-sm font-semibold text-gray-700">
            시스템 정보
          </h3>
          <div className="space-y-3 text-xs text-gray-600">
            <div>
              <div className="font-medium">Schema Version</div>
              <div>next4.v2</div>
            </div>
            <div>
              <div className="font-medium">API Endpoint</div>
              <div>POST /compare/view-model</div>
            </div>
            <div>
              <div className="font-medium">Renderer</div>
              <div>CompareViewModelRenderer</div>
            </div>
            <div className="mt-4 rounded-md bg-blue-50 p-3">
              <div className="font-medium text-blue-900 mb-1">
                Constitutional Principles
              </div>
              <ul className="list-inside list-disc space-y-1 text-blue-700">
                <li>Fact-only</li>
                <li>NO recommendation</li>
                <li>Evidence-based</li>
                <li>Deterministic</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
