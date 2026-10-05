import "./globals.css";

export const metadata = {
  title: "Librería | Análisis de catálogo",
  description: "Analiza y valida el inventario de libros desde un CSV.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}