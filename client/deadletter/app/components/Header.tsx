import { useAppContext } from '../contexts/AppContext';

export const Header = () => {
  const { user, logout } = useAppContext();
  const email = (user?.email ?? '') as string;
  return (
    <header className="mb-6 w-full flex flex-col md:flex-row md:items-center md:justify-between gap-2">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">📨 Dead Letter Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Monitor and manage failed Pub/Sub messages</p>
      </div>
      {user && (
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-600 max-w-[180px] truncate" title={email}>{email || 'No email'}</span>
          <button
            onClick={logout}
            className="px-3 py-1.5 text-xs font-medium bg-red-600 text-white rounded hover:bg-red-700 transition disabled:opacity-50"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
};