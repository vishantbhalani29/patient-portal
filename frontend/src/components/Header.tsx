import React from 'react';
import type { Role } from '../types/appointment';

interface HeaderProps {
  currentRole: Role;
  onRoleChange: (role: Role) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentRole, onRoleChange }) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
          </svg>
        </div>
        <div className="brand-titles">
          <h1>Patient Portal</h1>
          <span className="brand-tagline">Clinical Appointment Manager</span>
        </div>
      </div>

      <div className="header-actions">
        <div className="role-switcher-container">
          <span className="role-switcher-label">View Mode:</span>
          <div className="role-switcher">
            <button
              type="button"
              className={`role-btn ${currentRole === 'patient' ? 'active' : ''}`}
              onClick={() => onRoleChange('patient')}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              Patient View
            </button>
            <button
              type="button"
              className={`role-btn ${currentRole === 'provider' ? 'active' : ''}`}
              onClick={() => onRoleChange('provider')}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              Provider View
            </button>
          </div>
        </div>

        <div className="user-persona-badge">
          <span className="persona-dot"></span>
          <span className="persona-text">
            {currentRole === 'patient' ? 'Olivia Carter (patient-001)' : 'Dr. Ethan Brooks (provider-001)'}
          </span>
        </div>
      </div>
    </header>
  );
};
