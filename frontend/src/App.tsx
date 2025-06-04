import { AuthProvider } from '@/contexts/AuthProvider';
import Router from '@/router';
import '@/globals.css';

function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  );
}

export default App;
