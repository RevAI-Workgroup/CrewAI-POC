import { AuthProvider } from '@/contexts/AuthProvider';
import Router from '@/router';
import '@/globals.css';

import { Toaster } from "@/components/ui/sonner"

function App() {
  return (
    <AuthProvider>
      <Router />
      <Toaster />
    </AuthProvider>
  );
}

export default App;
