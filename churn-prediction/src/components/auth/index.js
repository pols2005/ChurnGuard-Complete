// Authentication Components
export { default as ProtectedRoute } from './ProtectedRoute';
export { default as UserProfile } from './UserProfile';
export { default as AuthLayout } from './AuthLayout';

// Main Login component (from parent directory)
export { default as Login } from '../Login';

// Re-export AuthContext for convenience
export { useAuth } from '../../contexts/AuthContext';