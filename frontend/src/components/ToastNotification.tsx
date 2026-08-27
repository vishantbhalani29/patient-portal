import React from 'react';

export interface ToastMessage {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
}

interface ToastNotificationProps {
  toast: ToastMessage | null;
  onDismiss: () => void;
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({ toast, onDismiss }) => {
  if (!toast) return null;

  return (
    <div className={`toast-banner toast-${toast.type}`}>
      <div className="toast-content">
        <span className="toast-icon">
          {toast.type === 'warning' || toast.type === 'error' ? '⚠️' : 'ℹ️'}
        </span>
        <span className="toast-message">{toast.message}</span>
      </div>
      <button type="button" className="toast-close" onClick={onDismiss}>
        &times;
      </button>
    </div>
  );
};
