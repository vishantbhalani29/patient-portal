import React, { useEffect, useState, useCallback } from 'react';
import type { Appointment, AppointmentCreateRequest } from '../types/appointment';
import { api, StaleError } from '../api/client';
import { AppointmentCard } from '../components/AppointmentCard';
import { CreateAppointmentModal } from '../components/CreateAppointmentModal';
import { ToastNotification, type ToastMessage } from '../components/ToastNotification';

export const PatientDashboard: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const loadAppointments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await api.getAppointments('patient', 'patient-001');
      setAppointments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch appointments.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAppointments();
  }, [loadAppointments]);

  const handleCreateAppointment = async (data: AppointmentCreateRequest) => {
    try {
      setIsSubmitting(true);
      await api.createAppointment(data);
      setToast({
        id: Date.now().toString(),
        type: 'success',
        message: 'Appointment request submitted successfully!',
      });
      await loadAppointments();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelAppointment = async (appointment: Appointment) => {
    try {
      setActionLoadingId(appointment.id);
      await api.cancelAppointment(appointment.id, {
        expected_version: appointment.version,
        actor_id: 'patient-001',
        actor_role: 'patient',
      });
      setToast({
        id: Date.now().toString(),
        type: 'info',
        message: `Appointment #${appointment.id} cancelled.`,
      });
      await loadAppointments();
    } catch (err: any) {
      if (err instanceof StaleError) {
        setToast({
          id: Date.now().toString(),
          type: 'warning',
          message: 'This appointment was updated. Refreshing...',
        });
        await loadAppointments();
      } else {
        setToast({
          id: Date.now().toString(),
          type: 'error',
          message: err.message || 'Failed to cancel appointment.',
        });
      }
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="dashboard-container">
      <ToastNotification toast={toast} onDismiss={() => setToast(null)} />

      <div className="dashboard-toolbar">
        <div>
          <h2>Patient Dashboard</h2>
          <p className="subtitle">Welcome back, Olivia. Manage your scheduled appointments and requests.</p>
        </div>
        <button
          type="button"
          className="btn btn-primary btn-lg"
          onClick={() => setIsModalOpen(true)}
        >
          + Request Appointment
        </button>
      </div>

      {isLoading && <div className="loading-state">Loading your appointments...</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {!isLoading && !error && appointments.length === 0 && (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <h3>No Appointments Found</h3>
          <p>You currently have no scheduled or requested appointments.</p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsModalOpen(true)}
          >
            Request Your First Appointment
          </button>
        </div>
      )}

      {!isLoading && appointments.length > 0 && (
        <div className="appointment-grid">
          {appointments.map((appt) => (
            <AppointmentCard
              key={appt.id}
              appointment={appt}
              currentRole="patient"
              onCancel={handleCancelAppointment}
              isActionLoading={actionLoadingId === appt.id}
            />
          ))}
        </div>
      )}

      <CreateAppointmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateAppointment}
        isLoading={isSubmitting}
      />
    </div>
  );
};
