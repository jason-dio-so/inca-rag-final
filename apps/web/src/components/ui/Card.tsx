/**
 * Card Component (UI primitive)
 */

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  severity?: 'success' | 'info' | 'warning' | 'error';
}

export function Card({ children, className = '', severity }: CardProps) {
  const severityColors = {
    success: 'border-green-500 bg-green-50',
    info: 'border-blue-500 bg-blue-50',
    warning: 'border-yellow-500 bg-yellow-50',
    error: 'border-red-500 bg-red-50',
  };

  const severityClass = severity ? severityColors[severity] : 'border-gray-300 bg-white';

  return (
    <div className={`border-2 rounded-lg p-6 ${severityClass} ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="mb-4">{children}</div>;
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-2xl font-bold mb-2">{children}</h2>;
}

export function CardDescription({ children }: { children: React.ReactNode }) {
  return <p className="text-gray-600 mb-4">{children}</p>;
}

export function CardContent({ children }: { children: React.ReactNode }) {
  return <div className="mb-4">{children}</div>;
}

export function CardFooter({ children }: { children: React.ReactNode }) {
  return <div className="flex gap-2 pt-4 border-t border-gray-200">{children}</div>;
}
