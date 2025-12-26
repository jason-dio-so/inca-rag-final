/**
 * Admin Mapping Workbench
 *
 * Purpose: Resolve UNMAPPED/AMBIGUOUS mapping events
 * Constitutional: Canonical Coverage Rule enforcement
 *
 * STEP NEXT-7: Admin UI for mapping resolution
 */

import { useState, useEffect } from 'react';
import type { GetServerSideProps } from 'next';

// ============================================================================
// Types
// ============================================================================

type EventState = 'OPEN' | 'APPROVED' | 'REJECTED' | 'SNOOZED';
type DetectedStatus = 'UNMAPPED' | 'AMBIGUOUS';
type ResolutionType = 'ALIAS' | 'NAME_MAP' | 'MANUAL_NOTE';

interface MappingEventSummary {
  id: string;
  created_at: string;
  updated_at: string;
  insurer: string;
  raw_coverage_title: string;
  detected_status: DetectedStatus;
  state: EventState;
  candidate_count: number;
}

interface MappingEventDetail {
  id: string;
  created_at: string;
  updated_at: string;
  insurer: string;
  query_text: string;
  normalized_query: string | null;
  raw_coverage_title: string;
  detected_status: DetectedStatus;
  candidate_coverage_codes: string[] | null;
  evidence_ref_ids: string[] | null;
  state: EventState;
  resolved_coverage_code: string | null;
  resolution_type: ResolutionType | null;
  resolution_note: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
}

// ============================================================================
// Main Component
// ============================================================================

export default function AdminMappingPage() {
  const [events, setEvents] = useState<MappingEventSummary[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<MappingEventDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [selectedCode, setSelectedCode] = useState('');
  const [resolutionType, setResolutionType] = useState<ResolutionType>('NAME_MAP');
  const [note, setNote] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  // Load event queue
  useEffect(() => {
    loadQueue();
  }, [page]);

  const loadQueue = async (filterState?: EventState) => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (filterState) {
        params.append('state', filterState);
      }

      const response = await fetch(`/api/admin/mapping/events?${params}`);

      if (!response.ok) {
        throw new Error(`Failed to load queue: ${response.statusText}`);
      }

      const data = await response.json();
      setEvents(data.events || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadEventDetail = async (eventId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/admin/mapping/events/${eventId}`);

      if (!response.ok) {
        throw new Error(`Failed to load event detail: ${response.statusText}`);
      }

      const data = await response.json();
      setSelectedEvent(data);

      // Pre-select first candidate code if available
      if (data.candidate_coverage_codes && data.candidate_coverage_codes.length > 0) {
        setSelectedCode(data.candidate_coverage_codes[0]);
      } else {
        setSelectedCode('');
      }

      // Reset form
      setNote('');
      setResolutionType('NAME_MAP');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedEvent || !selectedCode) {
      alert('Please select a coverage code');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/admin/mapping/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Actor': 'admin', // TODO: Replace with actual auth
        },
        body: JSON.stringify({
          event_id: selectedEvent.id,
          coverage_code: selectedCode,
          resolution_type: resolutionType,
          note: note || null,
          actor: 'admin', // TODO: Replace with actual auth
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Approval failed');
      }

      const result = await response.json();
      alert(`✅ Approved: ${result.message}`);

      // Reload queue and clear selection
      setSelectedEvent(null);
      loadQueue();
    } catch (err: any) {
      setError(err.message);
      alert(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedEvent) return;

    if (!confirm('Are you sure you want to reject this mapping?')) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/admin/mapping/reject', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Actor': 'admin',
        },
        body: JSON.stringify({
          event_id: selectedEvent.id,
          note: note || null,
          actor: 'admin',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Rejection failed');
      }

      alert('✅ Event rejected');
      setSelectedEvent(null);
      loadQueue();
    } catch (err: any) {
      setError(err.message);
      alert(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSnooze = async () => {
    if (!selectedEvent) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/admin/mapping/snooze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Actor': 'admin',
        },
        body: JSON.stringify({
          event_id: selectedEvent.id,
          note: note || null,
          actor: 'admin',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Snooze failed');
      }

      alert('✅ Event snoozed');
      setSelectedEvent(null);
      loadQueue();
    } catch (err: any) {
      setError(err.message);
      alert(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Admin Mapping Workbench
          </h1>
          <p className="text-gray-600 mt-2">
            Resolve UNMAPPED/AMBIGUOUS coverage mapping events
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Constitutional: Canonical Coverage Rule enforcement (신정원 통일코드)
          </p>
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Queue Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900">Event Queue</h2>
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => loadQueue('OPEN')}
                    className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    OPEN ({events.filter((e) => e.state === 'OPEN').length})
                  </button>
                  <button
                    onClick={() => loadQueue()}
                    className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    All
                  </button>
                </div>
              </div>

              <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                {loading && events.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">Loading...</div>
                ) : events.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">No events</div>
                ) : (
                  events.map((event) => (
                    <div
                      key={event.id}
                      onClick={() => loadEventDetail(event.id)}
                      className={`p-3 cursor-pointer hover:bg-gray-50 ${
                        selectedEvent?.id === event.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {event.raw_coverage_title}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {event.insurer}
                          </div>
                        </div>
                        <div className="flex flex-col items-end ml-2">
                          <span
                            className={`text-xs px-2 py-0.5 rounded ${
                              event.detected_status === 'UNMAPPED'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {event.detected_status}
                          </span>
                          <span className="text-xs text-gray-500 mt-1">
                            {event.state}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Pagination */}
              {total > pageSize && (
                <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="text-sm px-3 py-1 bg-gray-100 rounded disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {page} of {Math.ceil(total / pageSize)}
                  </span>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page * pageSize >= total}
                    className="text-sm px-3 py-1 bg-gray-100 rounded disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Detail Panel */}
          <div className="lg:col-span-2">
            {selectedEvent ? (
              <div className="bg-white rounded-lg shadow">
                <div className="px-4 py-3 border-b border-gray-200">
                  <h2 className="font-semibold text-gray-900">Event Detail</h2>
                </div>

                <div className="p-4 space-y-4">
                  {/* Event Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700">
                        Query Text
                      </label>
                      <div className="text-sm text-gray-900 mt-1">
                        {selectedEvent.query_text}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">
                        Insurer
                      </label>
                      <div className="text-sm text-gray-900 mt-1">
                        {selectedEvent.insurer}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">
                        Raw Coverage Title
                      </label>
                      <div className="text-sm text-gray-900 mt-1">
                        {selectedEvent.raw_coverage_title}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">
                        Status
                      </label>
                      <div className="text-sm text-gray-900 mt-1">
                        <span
                          className={`px-2 py-0.5 rounded ${
                            selectedEvent.detected_status === 'UNMAPPED'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {selectedEvent.detected_status}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Candidate Codes */}
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Candidate Coverage Codes (신정원 통일코드)
                    </label>
                    <div className="mt-2 space-y-2">
                      {selectedEvent.candidate_coverage_codes &&
                      selectedEvent.candidate_coverage_codes.length > 0 ? (
                        selectedEvent.candidate_coverage_codes.map((code) => (
                          <label
                            key={code}
                            className="flex items-center space-x-2 p-2 border rounded hover:bg-gray-50 cursor-pointer"
                          >
                            <input
                              type="radio"
                              name="coverage_code"
                              value={code}
                              checked={selectedCode === code}
                              onChange={(e) => setSelectedCode(e.target.value)}
                            />
                            <span className="text-sm font-mono text-gray-900">
                              {code}
                            </span>
                          </label>
                        ))
                      ) : (
                        <div className="text-sm text-gray-500">
                          No candidates (manual input required)
                        </div>
                      )}

                      {/* Manual input */}
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          placeholder="Or enter canonical code manually"
                          value={selectedCode}
                          onChange={(e) => setSelectedCode(e.target.value)}
                          className="flex-1 px-3 py-2 border rounded text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Resolution Type */}
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Resolution Type
                    </label>
                    <select
                      value={resolutionType}
                      onChange={(e) =>
                        setResolutionType(e.target.value as ResolutionType)
                      }
                      className="mt-1 block w-full px-3 py-2 border rounded text-sm"
                    >
                      <option value="NAME_MAP">NAME_MAP (담보명 매핑)</option>
                      <option value="ALIAS">ALIAS (별칭 등록)</option>
                      <option value="MANUAL_NOTE">MANUAL_NOTE (수동 메모)</option>
                    </select>
                  </div>

                  {/* Note */}
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Note (Optional)
                    </label>
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      rows={3}
                      className="mt-1 block w-full px-3 py-2 border rounded text-sm"
                      placeholder="Add resolution note..."
                    />
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3 pt-4 border-t">
                    <button
                      onClick={handleApprove}
                      disabled={loading || !selectedCode}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={loading}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                    >
                      Reject
                    </button>
                    <button
                      onClick={handleSnooze}
                      disabled={loading}
                      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                    >
                      Snooze
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                Select an event from the queue to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
