import type { Metadata } from 'next';
import '../styles/app.css';

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
      <body>
        <div className="max-w-screen-xl mx-auto px-4 py-8">
          {children}
        </div>
      </body>
    </html>
  );
}
