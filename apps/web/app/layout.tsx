import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MyFlightbook v1",
  description: "Greenfield migration workspace for the next MyFlightbook web experience."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
