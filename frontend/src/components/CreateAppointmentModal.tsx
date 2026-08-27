import React, { useState } from 'react';
import type { AppointmentCreateRequest } from '../types/appointment';
import { datetimeLocalToUtc } from '../utils/datetime';

interface CreateAppointmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AppointmentCreateRequest) => Promise<void>;
  isLoading: boolean;
}

export const CreateAppointmentModal: React.FC<CreateAppointmentModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}) => {
  const [appointmentType, setAppointmentType] = useState('Medication Review');
  const [requestedStart, setRequestedStart] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestedStart) {
      setError('Please select a preferred date and time.');
      return;
    }

    try {
      setError(null);
      // Convert IST datetime-local input value to ISO UTC string
      const utcIsoDate = datetimeLocalToUtc(requestedStart);
      await onSubmit({
        patient_id: 'patient-001',
        patient_name: 'Olivia Carter',
        patient_email: 'olivia.carter@email.test',
        provider_id: 'provider-001',
        provider_name: 'Dr. Ethan Brooks',
        appointment_type: appointmentType,
        reason: reason || undefined,
        requested_start: utcIsoDate,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to request appointment.');
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <h2>Request New Appointment</h2>
          <button type="button" className="close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="alert alert-error">{error}</div>}

            <div className="form-group">
              <label htmlFor="provider">Provider</label>
              <input
                id="provider"
                type="text"
                value="Dr. Ethan Brooks"
                disabled
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="appointmentType">Appointment Type</label>
              <select
                id="appointmentType"
                value={appointmentType}
                onChange={(e) => setAppointmentType(e.target.value)}
                className="form-control"
              >
                <option value="Behavioral Health Intake">Behavioral Health Intake</option>
                <option value="Medication Review">Medication Review</option>
                <option value="Counseling Session">Counseling Session</option>
                <option value="General Consultation">General Consultation</option>
                <option value="Follow-up Visit">Follow-up Visit</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="requestedStart">Preferred Date & Time (IST)</label>
              <input
                id="requestedStart"
                type="datetime-local"
                value={requestedStart}
                onChange={(e) => setRequestedStart(e.target.value)}
                required
                className="form-control"
              />
              <span className="field-help">Times are selected in Indian Standard Time (IST). Duration: 30 minutes.</span>
            </div>

            <div className="form-group">
              <label htmlFor="reason">Reason for Visit (Optional)</label>
              <textarea
                id="reason"
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Briefly describe your symptoms or request..."
                className="form-control"
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
