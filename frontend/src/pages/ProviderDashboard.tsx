import React, { useEffect, useState, useCallback } from 'react';
import type { Appointment } from '../types/appointment';
import { api, StaleError, ScheduleConflictError } from '../api/client';
import { AppointmentCard } from '../components/AppointmentCard';
import { RescheduleModal } from '../components/RescheduleModal';
import { HistoryModal } from '../components/HistoryModal';
import { ToastNotification, type ToastMessage } from '../components/ToastNotification';

export const ProviderDashboard: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRescheduleAppt, setSelectedRescheduleAppt] = useState<Appointment | null>(null);
  const [selectedHistoryAppt, setSelectedHistoryAppt] = useState<Appointment | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const loadAppointments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await api.getAppointments('provider', 'provider-001');
      setAppointments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch schedule.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAppointments();
  }, [loadAppointments]);

  const handleConfirm = async (appointment: Appointment) => {
    try {
      setActionLoadingId(appointment.id);
      await api.confirmAppointment(appointment.id, {
        expected_version: appointment.version,
        actor_id: 'provider-001',
        actor_role: 'provider',
      });
      setToast({
        id: Date.now().toString(),
        type: 'success',
        message: `Appointment #${appointment.id} confirmed successfully.`,
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
      } else if (err instanceof ScheduleConflictError) {
        setToast({
          id: Date.now().toString(),
          type: 'error',
          message: err.message,
        });
        await loadAppointments();
      } else {
        setToast({
          id: Date.now().toString(),
          type: 'error',
          message: err.message || 'Failed to confirm appointment.',
        });
      }
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRescheduleSubmit = async (id: number, expectedVersion: number, newStart: string) => {
    try {
      setIsSubmitting(true);
      await api.rescheduleAppointment(id, {
        expected_version: expectedVersion,
        scheduled_start: newStart,
        actor_id: 'provider-001',
        actor_role: 'provider',
      });
      setToast({
        id: Date.now().toString(),
        type: 'info',
        message: `Appointment #${id} rescheduled successfully.`,
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
      } else if (err instanceof ScheduleConflictError) {
        setToast({
          id: Date.now().toString(),
          type: 'error',
          message: err.message,
        });
        await loadAppointments();
      } else {
        throw err;
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="dashboard-container">
      <ToastNotification toast={toast} onDismiss={() => setToast(null)} />

      <div className="dashboard-toolbar">
        <div>
          <h2>Provider Schedule & Management</h2>
          <p className="subtitle">Welcome, Dr. Brooks. Review pending requests, manage schedule slots, and inspect change history.</p>
        </div>
      </div>

      {isLoading && <div className="loading-state">Loading provider schedule...</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {!isLoading && !error && appointments.length === 0 && (
        <div className="empty-state">
          <h3>No Provider Appointments</h3>
          <p>There are no appointments registered in your schedule.</p>
        </div>
      )}

      {!isLoading && appointments.length > 0 && (
        <div className="appointment-grid">
          {appointments.map((appt) => (
            <AppointmentCard
              key={appt.id}
              appointment={appt}
              currentRole="provider"
              onConfirm={handleConfirm}
              onReschedule={(a) => setSelectedRescheduleAppt(a)}
              onViewHistory={(a) => setSelectedHistoryAppt(a)}
              isActionLoading={actionLoadingId === appt.id}
            />
          ))}
        </div>
      )}

      <RescheduleModal
        isOpen={Boolean(selectedRescheduleAppt)}
        appointment={selectedRescheduleAppt}
        onClose={() => setSelectedRescheduleAppt(null)}
        onSubmit={handleRescheduleSubmit}
        isLoading={isSubmitting}
      />

      <HistoryModal
        isOpen={Boolean(selectedHistoryAppt)}
        appointment={selectedHistoryAppt}
        onClose={() => setSelectedHistoryAppt(null)}
      />
    </div>
  );
};
