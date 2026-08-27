export type AppointmentStatus = 'pending' | 'confirmed' | 'cancelled';

export type Role = 'patient' | 'provider';

export interface Appointment {
  id: number;
  patient_id: string;
  patient_name: string;
  patient_email: string;
  provider_id: string;
  provider_name: string;
  appointment_type: string;
  reason?: string | null;
  requested_start: string;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  status: AppointmentStatus;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: number;
  appointment_id: number;
  actor_id: string;
  actor_role: string;
  action: string;
  before_state?: Record<string, any> | null;
  after_state?: Record<string, any> | null;
  created_at: string;
}

export interface AppointmentCreateRequest {
  patient_id: string;
  patient_name: string;
  patient_email: string;
  provider_id: string;
  provider_name: string;
  appointment_type: string;
  reason?: string;
  requested_start: string;
}

export interface AppointmentConfirmRequest {
  expected_version: number;
  scheduled_start?: string;
  actor_id?: string;
  actor_role?: string;
}

export interface AppointmentRescheduleRequest {
  expected_version: number;
  scheduled_start: string;
  actor_id?: string;
  actor_role?: string;
}

export interface AppointmentCancelRequest {
  expected_version: number;
  actor_id?: string;
  actor_role?: string;
}

export interface ApiErrorDetail {
  code?: string;
  message?: string;
  current_version?: number;
  detail?: string | any;
}
