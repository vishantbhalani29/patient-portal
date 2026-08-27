import React from 'react';
import type { Appointment, Role } from '../types/appointment';
import { formatUtcToIST } from '../utils/datetime';

interface AppointmentCardProps {
  appointment: Appointment;
  currentRole: Role;
  onConfirm?: (appointment: Appointment) => void;
  onReschedule?: (appointment: Appointment) => void;
  onCancel?: (appointment: Appointment) => void;
  onViewHistory?: (appointment: Appointment) => void;
  isActionLoading?: boolean;
}

export const AppointmentCard: React.FC<AppointmentCardProps> = ({
  appointment,
  currentRole,
  onConfirm,
  onReschedule,
  onCancel,
  onViewHistory,
  isActionLoading,
}) => {
  const statusBadgeClass = `status-badge status-${appointment.status}`;

  return (
    <div className="appointment-card">
      <div className="card-header">
        <div className="card-title-group">
          <h3 className="appointment-type">{appointment.appointment_type}</h3>
          <div className="meta-pills">
            <span className={statusBadgeClass}>{appointment.status}</span>
            <span className="version-pill">v{appointment.version}</span>
          </div>
        </div>
      </div>

      <div className="card-body">
        <div className="info-row">
          <div className="info-item">
            <span className="info-label">
              {currentRole === 'patient' ? 'Healthcare Provider' : 'Patient Name'}
            </span>
            <span className="info-value">
              {currentRole === 'patient' ? appointment.provider_name : appointment.patient_name}
            </span>
          </div>
          {currentRole === 'provider' && (
            <div className="info-item">
              <span className="info-label">Patient Email</span>
              <span className="info-value">{appointment.patient_email}</span>
            </div>
          )}
        </div>

        <div className="info-row">
          <div className="info-item">
            <span className="info-label">Scheduled Time Slot (IST)</span>
            <span className="info-value highlight">
              {formatUtcToIST(appointment.scheduled_start || appointment.requested_start)}
            </span>
          </div>
        </div>

        {appointment.reason && (
          <div className="info-row">
            <div className="info-item">
              <span className="info-label">Reason for Visit</span>
              <p className="info-notes">{appointment.reason}</p>
            </div>
          </div>
        )}
      </div>

      <div className="card-actions">
        {/* Provider Actions */}
        {currentRole === 'provider' && (
          <>
            {appointment.status === 'pending' && (
              <button
                type="button"
                className="btn btn-success"
                disabled={isActionLoading}
                onClick={() => onConfirm?.(appointment)}
              >
                Confirm Request
              </button>
            )}
            {appointment.status !== 'cancelled' && (
              <button
                type="button"
                className="btn btn-secondary"
                disabled={isActionLoading}
                onClick={() => onReschedule?.(appointment)}
              >
                Reschedule
              </button>
            )}
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => onViewHistory?.(appointment)}
            >
              View History
            </button>
          </>
        )}

        {/* Patient Actions */}
        {currentRole === 'patient' && (
          <>
            {appointment.status === 'confirmed' && (
              <button
                type="button"
                className="btn btn-danger"
                disabled={isActionLoading}
                onClick={() => onCancel?.(appointment)}
              >
                Cancel Appointment
              </button>
            )}
            {appointment.status === 'pending' && (
              <span className="pending-note">
                Awaiting provider confirmation. Cannot cancel pending request.
              </span>
            )}
            {appointment.status === 'cancelled' && (
              <span className="cancelled-note">This appointment has been cancelled.</span>
            )}
          </>
        )}
      </div>
    </div>
  );
};
