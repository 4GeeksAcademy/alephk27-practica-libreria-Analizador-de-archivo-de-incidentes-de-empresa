import csv
import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from analyze import summarize_books, write_results_csv


REQUIRED_COLUMNS = {"isbn", "titulo", "genero", "precio", "stock", "status"}

app = FastAPI(title="Analizador de libros")
app.state.last_analysis = None


@app.post("/api/books/analyze")
async def analyze_uploaded_books(upload_file: UploadFile = File(..., alias="uploadFile")):
    content = await upload_file.read()
    await upload_file.close()

    if not content:
        raise HTTPException(status_code=400, detail="El archivo CSV esta vacio")

    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=404,
            detail=f"Formato CSV invalido: no se pudo leer UTF-8 ({error})",
        ) from error

    try:
        reader = csv.DictReader(io.StringIO(csv_text, newline=""), strict=True)
        if not reader.fieldnames:
            raise HTTPException(status_code=404, detail="Formato CSV invalido: falta la cabecera")

        headers = [header.strip().casefold() if header else "" for header in reader.fieldnames]
        if any(not header for header in headers) or len(headers) != len(set(headers)):
            raise HTTPException(status_code=404, detail="Formato CSV invalido: cabecera vacia o duplicada")

        missing_columns = sorted(REQUIRED_COLUMNS - set(headers))
        if missing_columns:
            raise HTTPException(
                status_code=404,
                detail=f"Formato CSV invalido: faltan columnas {', '.join(missing_columns)}",
            )

        reader.fieldnames = headers
        books = []
        for row_number, book in enumerate(reader, start=2):
            if None in book or any(value is None for value in book.values()):
                raise HTTPException(
                    status_code=404,
                    detail=f"Formato CSV invalido en la fila {row_number}: numero de columnas incorrecto",
                )
            books.append(book)
    except csv.Error as error:
        raise HTTPException(status_code=404, detail=f"Formato CSV invalido: {error}") from error

    if not books:
        raise HTTPException(status_code=404, detail="Formato CSV invalido: no hay registros")

    results = summarize_books(books)
    results["genres"] = dict(results["genres"])
    results["statuses"] = dict(results["statuses"])
    app.state.last_analysis = results
    return results


@app.get("/api/books/results/export")
def export_last_analysis():
    results = app.state.last_analysis
    if results is None:
        raise HTTPException(status_code=404, detail="Todavia no hay un analisis para exportar")

    csv_output = io.StringIO(newline="")
    write_results_csv(results, csv_output)
    csv_output.seek(0)
    return StreamingResponse(
        iter([csv_output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )
