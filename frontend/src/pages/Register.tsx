import React from 'react';
import { RegistrationForm } from '../components/auth/registration-form';

export function RegisterPage() {
  return (
    <div className="bg-background flex min-h-svh flex-col items-center justify-center gap-6 p-6 md:p-10">
      <div className="w-full max-w-sm">
        <RegistrationForm />
      </div>
    </div>
  );
}
