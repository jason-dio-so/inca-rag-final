/**
 * Button Component (UI primitive)
 */

import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
  disabled?: boolean;
  className?: string;
  size?: string;
}

export function Button({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = '',
  size = 'md',
}: ButtonProps) {
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700',
    outline: 'bg-white text-blue-600 border-2 border-blue-600 hover:bg-blue-50',
  };

  const baseClasses = 'px-4 py-2 rounded-md font-medium transition-colors';
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${disabledClasses} ${className}`}
    >
      {children}
    </button>
  );
}
