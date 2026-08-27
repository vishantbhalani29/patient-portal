import React, { useEffect, useState } from 'react';
import type { Appointment, AuditEvent } from '../types/appointment';
import { api } from '../api/client';
import { formatUtcToIST } from '../utils/datetime';

interface HistoryModalProps {
  appointment: Appointment | null;
  isOpen: boolean;
  onClose: () => void;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({ appointment, isOpen, onClose }) => {
  const [history, setHistory] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && appointment) {
      setIsLoading(true);
      setError(null);
      api
        .getHistory(appointment.id)
        .then((data) => setHistory(data))
        .catch((err) => setError(err.message || 'Failed to load audit history.'))
        .finally(() => setIsLoading(false));
    } else {
      setHistory([]);
    }
  }, [isOpen, appointment]);

  if (!isOpen || !appointment) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog modal-lg">
        <div className="modal-header">
          <div>
            <h2>Appointment History #{appointment.id}</h2>
            <span className="subtitle">
              {appointment.patient_name} — {appointment.appointment_type}
            </span>
          </div>
          <button type="button" className="close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {isLoading && <div className="loading-spinner">Loading audit timeline...</div>}
          {error && <div className="alert alert-error">{error}</div>}

          {!isLoading && !error && history.length === 0 && (
            <p className="empty-text">No audit events recorded for this appointment.</p>
          )}

          {!isLoading && history.length > 0 && (
            <div className="history-timeline">
              {history.map((event, index) => {
                const before = event.before_state || {};
                const after = event.after_state || {};
                return (
                  <div key={event.id || index} className="timeline-item">
                    <div className="timeline-marker">
                      <span className={`action-badge action-${event.action}`}>
                        {event.action}
                      </span>
                    </div>

                    <div className="timeline-content">
                      <div className="timeline-header">
                        <span className="actor-info">
                          By <strong>{event.actor_id}</strong> ({event.actor_role})
                        </span>
                        <span className="timestamp">{formatUtcToIST(event.created_at)}</span>
                      </div>

                      <div className="state-changes">
                        <div className="change-row">
                          <span className="change-label">Status:</span>
                          <span className="change-detail">
                            {before.status ? (
                              <>
                                <span className={`status-pill status-${before.status}`}>
                                  {before.status}
                                </span>{' '}
                                &rarr;{' '}
                              </>
                            ) : null}
                            <span className={`status-pill status-${after.status}`}>
                              {after.status}
                            </span>
                          </span>
                        </div>

                        {(before.scheduled_start || after.scheduled_start) && (
                          <div className="change-row">
                            <span className="change-label">Schedule:</span>
                            <span className="change-detail">
                              {before.scheduled_start ? (
                                <>{formatUtcToIST(before.scheduled_start)} &rarr; </>
                              ) : null}
                              {formatUtcToIST(after.scheduled_start)}
                            </span>
                          </div>
                        )}

                        <div className="change-row">
                          <span className="change-label">Version:</span>
                          <span className="change-detail">
                            {before.version !== undefined ? `v${before.version} → ` : ''}v{after.version}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-outline" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
