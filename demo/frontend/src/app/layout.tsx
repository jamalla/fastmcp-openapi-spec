import "./globals.css";

export const metadata = {
  title: "وكيل سلة الذكي",
  description: "وكيل ذكي لواجهة برمجة تطبيقات سلة",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
