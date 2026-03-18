import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../styles/app.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MusicApp - Sheet Music Transposition',
  description: 'AI-guided transposition for musicians',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-slate-50 text-slate-900`}>
        <div className="max-w-screen-xl mx-auto px-4 py-8">
          {children}
        </div>
      </body>
    </html>
  );
}
