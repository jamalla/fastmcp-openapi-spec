import "./globals.css";

export const metadata = {
  title: "Salla API Agent",
  description: "AI agent for the Salla e-commerce API",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
