import React, { useState, useEffect } from 'react';
import type { Appointment } from '../types/appointment';
import { utcToDatetimeLocal, datetimeLocalToUtc } from '../utils/datetime';

interface RescheduleModalProps {
  appointment: Appointment | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (id: number, expectedVersion: number, newStart: string) => Promise<void>;
  isLoading: boolean;
}

export const RescheduleModal: React.FC<RescheduleModalProps> = ({
  appointment,
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}) => {
  const [newStart, setNewStart] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (appointment?.scheduled_start || appointment?.requested_start) {
      // Convert stored UTC string into datetime-local IST value for editing
      const localIstValue = utcToDatetimeLocal(
        appointment.scheduled_start || appointment.requested_start
      );
      setNewStart(localIstValue);
    } else {
      setNewStart('');
    }
    setError(null);
  }, [appointment]);

  if (!isOpen || !appointment) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStart) {
      setError('Please select a new date and time.');
      return;
    }

    try {
      setError(null);
      // Convert user's selected IST datetime-local value to ISO UTC string
      const utcIsoDate = datetimeLocalToUtc(newStart);
      await onSubmit(appointment.id, appointment.version, utcIsoDate);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to reschedule appointment.');
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <h2>Reschedule Appointment #{appointment.id}</h2>
          <button type="button" className="close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="alert alert-error">{error}</div>}

            <div className="info-summary">
              <p><strong>Patient:</strong> {appointment.patient_name}</p>
              <p><strong>Type:</strong> {appointment.appointment_type}</p>
              <p><strong>Current Version:</strong> v{appointment.version}</p>
            </div>

            <div className="form-group">
              <label htmlFor="newStart">New Date & Time (IST)</label>
              <input
                id="newStart"
                type="datetime-local"
                value={newStart}
                onChange={(e) => setNewStart(e.target.value)}
                required
                className="form-control"
              />
              <span className="field-help">Time selected in IST. Appointment duration: 30 minutes.</span>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Confirm Reschedule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
