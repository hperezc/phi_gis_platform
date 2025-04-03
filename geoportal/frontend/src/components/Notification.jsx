export default function Notification({ message, type = 'error', onClose }) {
  return (
    <div className={`notification ${type}`}>
      <div className="notification-content">
        <span>{message}</span>
        <button onClick={onClose}>&times;</button>
      </div>
    </div>
  );
} 