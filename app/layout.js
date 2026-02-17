export const metadata = {
  title: 'Power Benchmarking Suite',
  description: 'Monitor and analyze power consumption on Apple Silicon',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
