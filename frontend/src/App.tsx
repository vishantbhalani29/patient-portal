import { useState } from 'react';
import type { Role } from './types/appointment';
import { Header } from './components/Header';
import { PatientDashboard } from './pages/PatientDashboard';
import { ProviderDashboard } from './pages/ProviderDashboard';
import './App.css';

function App() {
  const [currentRole, setCurrentRole] = useState<Role>('patient');

  return (
    <div className="app-container">
      <Header currentRole={currentRole} onRoleChange={(role) => setCurrentRole(role)} />

      <main className="main-content">
        {currentRole === 'patient' ? (
          <PatientDashboard key="patient" />
        ) : (
          <ProviderDashboard key="provider" />
        )}
      </main>

      <footer className="app-footer">
        <p>Patient Portal App &copy; 2026 — Built with React, TypeScript &amp; FastAPI</p>
      </footer>
    </div>
  );
}

export default App;
