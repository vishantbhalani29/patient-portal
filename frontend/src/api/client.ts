import type {
  Appointment,
  AuditEvent,
  AppointmentCreateRequest,
  AppointmentConfirmRequest,
  AppointmentRescheduleRequest,
  AppointmentCancelRequest,
  Role,
} from '../types/appointment';

export class StaleError extends Error {
  currentVersion?: number;
  constructor(message: string, currentVersion?: number) {
    super(message);
    this.name = 'StaleError';
    this.currentVersion = currentVersion;
  }
}

export class ScheduleConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ScheduleConflictError';
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }

    if (response.status === 409) {
      if (errorData.code === 'STALE_APPOINTMENT') {
        throw new StaleError(
          errorData.message || 'This appointment was updated by another user.',
          errorData.current_version
        );
      }
      if (errorData.code === 'PROVIDER_SCHEDULE_CONFLICT') {
        throw new ScheduleConflictError(
          errorData.message || 'The provider already has a confirmed appointment during this time.'
        );
      }
    }

    const message =
      typeof errorData.detail === 'string'
        ? errorData.detail
        : errorData.message || `Request failed with status ${response.status}`;

    throw new ApiError(response.status, message);
  }

  return response.json();
}

export const api = {
  getAppointments: (role: Role, userId: string): Promise<Appointment[]> => {
    return request<Appointment[]>(`/api/appointments?role=${role}&user_id=${userId}`);
  },

  getHistory: (id: number): Promise<AuditEvent[]> => {
    return request<AuditEvent[]>(`/api/appointments/${id}/history`);
  },

  createAppointment: (data: AppointmentCreateRequest): Promise<Appointment> => {
    return request<Appointment>('/api/appointments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  confirmAppointment: (id: number, data: AppointmentConfirmRequest): Promise<Appointment> => {
    return request<Appointment>(`/api/appointments/${id}/confirm`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  rescheduleAppointment: (id: number, data: AppointmentRescheduleRequest): Promise<Appointment> => {
    return request<Appointment>(`/api/appointments/${id}/reschedule`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  cancelAppointment: (id: number, data: AppointmentCancelRequest): Promise<Appointment> => {
    return request<Appointment>(`/api/appointments/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
