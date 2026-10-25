'use client';

import type { ReactNode } from 'react';
import { ThemeProvider } from 'next-themes';

/**
 * Tema de los backoffices (plataforma y club): `next-themes` aplica `.dark` en
 * <html> segun la preferencia del sistema. Los tokens de `backoffice.css` ya
 * definen ambos modos, asi que no hace falta un control visible.
 */
export function AppThemeProvider({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </ThemeProvider>
  );
}
