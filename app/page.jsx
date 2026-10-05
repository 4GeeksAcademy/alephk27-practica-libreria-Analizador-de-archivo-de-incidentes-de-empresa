"use client";

import { useRef, useState } from "react";

const money = new Intl.NumberFormat("es-ES", {
  style: "currency",
  currency: "EUR",
});

function Distribution({ title, items, kind }) {
  const largest = Math.max(1, ...items.map(([, count]) => count));

  return (
    <section className="distribution-panel">
      <div className="section-heading">
        <div>
          <span className="section-kicker">DISTRIBUCIÓN</span>
          <h2>{title}</h2>
        </div>
        <span className="item-count">{items.length} categorías</span>
      </div>
      {items.length ? (
        <div className="distribution-list">
          {items.map(([label, count]) => (
            <div className="distribution-row" key={label}>
              <div className="distribution-label">
                <span>{label}</span>
                <strong>{count}</strong>
              </div>
              <div className={`bar-track ${kind}`}>
                <span style={{ width: `${Math.max(4, (count / largest) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-note">Sin datos para mostrar.</p>
      )}
    </section>
  );
}

export default function Home() {
  const inputRef = useRef(null);
  const [result, setResult] = useState(null);
  const [filename, setFilename] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [downloading, setDownloading] = useState(false);

  async function analyzeFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Selecciona un archivo con extensión .csv.");
      return;
    }

    setFilename(file.name);
    setError("");
    setBusy(true);
    setResult(null);

    const body = new FormData();
    body.append("uploadFile", file);

    try {
      const response = await fetch("/api/books/analyze", {
        method: "POST",
        body,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "No se pudo analizar el archivo.");
      }
      setResult(data);
    } catch (requestError) {
      setError(requestError.message || "No se pudo conectar con el analizador.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function downloadResults() {
    setError("");
    setDownloading(true);
    try {
      const response = await fetch("/api/books/results/export");
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "No se pudo descargar el CSV.");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "results.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.message || "No se pudo descargar el CSV.");
    } finally {
      setDownloading(false);
    }
  }

  const invalidCount = result ? result.total_books - result.valid_books : 0;
  const genreItems = result ? Object.entries(result.genres || {}) : [];
  const statusItems = result ? Object.entries(result.statuses || {}) : [];

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Librería, inicio">
          <span className="brand-mark"><span /></span>
          <span>LIBRERÍA<span className="brand-dot">.</span></span>
        </a>
        <div className="topbar-meta">
          <span className="live-dot" />
          <span>ANÁLISIS DE CATÁLOGO</span>
        </div>
      </header>

      <div className="page-content">
        <section className="intro">
          <div>
            <p className="eyebrow">CONTROL DE INVENTARIO <span>/</span> CSV</p>
            <h1>Tu catálogo,<br /><em>en claro.</em></h1>
          </div>
          <p className="intro-copy">Valida registros, detecta inconsistencias y entiende el estado de tu inventario.</p>
        </section>

        <section className="upload-section" aria-label="Cargar archivo CSV">
          <label
            className={`dropzone${dragging ? " is-dragging" : ""}${busy ? " is-busy" : ""}`}
            htmlFor="csv-file"
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              analyzeFile(event.dataTransfer.files[0]);
            }}
          >
            <input
              ref={inputRef}
              id="csv-file"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => analyzeFile(event.target.files[0])}
              disabled={busy}
            />
            <span className="upload-icon" aria-hidden="true">CSV</span>
            <span className="dropzone-copy">
              <strong>{busy ? "Analizando archivo..." : filename || "Suelta tu archivo CSV aquí"}</strong>
              <span>{busy ? "Validando registros y calculando métricas" : "o haz clic para buscar en tu equipo"}</span>
            </span>
            <span className="choose-file">{busy ? <span className="spinner" /> : "Seleccionar archivo"}</span>
          </label>
          <p className="upload-hint">Formato admitido: CSV · Cabeceras: isbn, titulo, genero, precio, stock, status</p>
        </section>

        {error && <p className="error-banner" role="alert">{error}</p>}

        {result ? (
          <section className="results" aria-live="polite">
            <div className="results-heading">
              <div>
                <p className="eyebrow">RESULTADO DEL ANÁLISIS</p>
                <h2>Resumen del catálogo</h2>
                <p className="source-file">Archivo procesado: <strong>{filename}</strong></p>
              </div>
              <button className="download-button" onClick={downloadResults} disabled={downloading}>
                {downloading ? "Preparando..." : "Descargar resultados CSV"}
                <span aria-hidden="true">↓</span>
              </button>
            </div>

            <div className="metrics" aria-label="Indicadores principales">
              <article className="metric metric-valid">
                <span className="metric-label"><i /> REGISTROS VÁLIDOS</span>
                <strong>{result.valid_books}</strong>
                <span className="metric-note">de {result.total_books} registros</span>
              </article>
              <article className="metric metric-invalid">
                <span className="metric-label"><i /> REGISTROS INVÁLIDOS</span>
                <strong>{invalidCount}</strong>
                <span className="metric-note">requieren revisión</span>
              </article>
              <article className="metric metric-price">
                <span className="metric-label"><i /> PRECIO MEDIO</span>
                <strong>{money.format(Number(result.average_price || 0))}</strong>
                <span className="metric-note">solo registros válidos</span>
              </article>
              <article className="metric metric-total">
                <span className="metric-label"><i /> VALOR INVENTARIO</span>
                <strong>{money.format(Number(result.inventory_value || 0))}</strong>
                <span className="metric-note">precio × stock</span>
              </article>
            </div>

            <div className="breakdowns">
              <Distribution title="Géneros" items={genreItems} kind="genre" />
              <Distribution title="Estado del catálogo" items={statusItems} kind="status" />
            </div>

            <section className="invalid-section">
              <div className="section-heading invalid-heading">
                <div>
                  <span className="section-kicker">REVISIÓN DE DATOS</span>
                  <h2>Registros inválidos <span className="count-badge">{invalidCount}</span></h2>
                </div>
                {invalidCount > 0 && <span className="invalid-caption">Cada fila incluye sus motivos de validación</span>}
              </div>
              {result.validation_errors?.length ? (
                <div className="invalid-list">
                  {result.validation_errors.map((entry) => {
                    const record = entry.registro || {};
                    return (
                      <article className="invalid-row" key={`${entry.fila}-${record.isbn || "registro"}`}>
                        <div className="invalid-row-heading">
                          <span className="row-number">FILA {entry.fila}</span>
                          <strong>{record.titulo || "Sin título"}</strong>
                        </div>
                        <dl className="record-fields">
                          <div><dt>ISBN</dt><dd>{record.isbn || "—"}</dd></div>
                          <div><dt>GÉNERO</dt><dd>{record.genero || "—"}</dd></div>
                          <div><dt>PRECIO</dt><dd>{record.precio || "—"}</dd></div>
                          <div><dt>STOCK</dt><dd>{record.stock || "—"}</dd></div>
                          <div><dt>ESTADO</dt><dd>{record.status || "—"}</dd></div>
                        </dl>
                        <ul className="reason-list">
                          {entry.motivos.map((reason, index) => <li key={`${entry.fila}-${index}`}>{reason}</li>)}
                        </ul>
                      </article>
                    );
                  })}
                </div>
              ) : (
                <p className="all-valid"><span>✓</span> Todos los registros pasaron la validación.</p>
              )}
            </section>
          </section>
        ) : (
          <section className="empty-state" aria-live="polite">
            <span className="empty-rule" />
            <p>{busy ? "El análisis aparecerá aquí al terminar." : "Carga un archivo para ver el estado de tu catálogo."}</p>
            <span>ESPERANDO ARCHIVO</span>
          </section>
        )}
      </div>
      <footer className="footer"><span>LIBRERÍA / HERRAMIENTAS DE INVENTARIO</span><span>CSV ANALYZER <b>01</b></span></footer>
    </main>
  );
}