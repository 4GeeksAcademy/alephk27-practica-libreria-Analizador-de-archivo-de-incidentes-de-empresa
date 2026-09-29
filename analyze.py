import argparse
import csv
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


VALID_GENRES = {
    "arte",
    "aventura",
    "biografia",
    "ciencia",
    "ciencia ficcion",
    "cocina",
    "drama",
    "fantasia",
    "historia",
    "infantil",
    "misterio",
    "novela",
    "viajes",
}
VALID_STATUSES = {"disponible", "agotado", "dañado"}


def validate_books(books):
    valid_books = []
    errors = []

    for row_number, book in enumerate(books, start=2):
        row_errors = []
        title = (book.get("titulo") or "").strip()
        genre = (book.get("genero") or "").strip().casefold()
        status = (book.get("status") or "").strip().casefold()
        price_text = (book.get("precio") or "").strip()

        if not title:
            row_errors.append("titulo vacio")
        if not genre:
            row_errors.append("genero vacio")
        elif genre not in VALID_GENRES:
            row_errors.append(f"genero no permitido: {book.get('genero')}")
        if not price_text:
            row_errors.append("precio vacio")
        else:
            try:
                price = Decimal(price_text)
                if not price.is_finite() or price < 0:
                    row_errors.append("precio debe ser un numero mayor o igual a 0")
            except InvalidOperation:
                row_errors.append(f"precio no numerico: {price_text}")
        if not status:
            row_errors.append("status vacio")
        elif status not in VALID_STATUSES:
            row_errors.append(f"status no permitido: {book.get('status')}")

        if row_errors:
            errors.append({"fila": row_number, "motivos": row_errors})
        else:
            valid_books.append(book)

    return valid_books, errors


def calculate_inventory_value(books):
    total = Decimal("0.00")
    for book in books:
        try:
            price = Decimal(book.get("precio") or "0")
            stock = int(book.get("stock") or 0)
        except (InvalidOperation, ValueError):
            continue
        total += price * stock
    return total


def summarize_books(books):
    valid_books, validation_errors = validate_books(books)
    inventory_value = calculate_inventory_value(books)
    missing_titles = 0
    genres = Counter()
    statuses = Counter()

    for book in books:
        title = (book.get("titulo") or "").strip()
        if not title:
            missing_titles += 1

        genres[(book.get("genero") or "").strip() or "Sin genero"] += 1
        statuses[(book.get("status") or "").strip() or "Sin status"] += 1

    results = {
        "total_books": len(books),
        "valid_books": len(valid_books),
        "validation_errors": validation_errors,
        "inventory_value": f"{inventory_value:.2f}",
        "missing_titles": missing_titles,
        "genres": genres,
        "statuses": statuses,
    }
    return results


def analyze_books(csv_path):
    with open(csv_path, mode="r", newline="", encoding="utf-8") as csv_file:
        books = list(csv.DictReader(csv_file))

    results = summarize_books(books)
    print_summary(results)
    return results


def print_summary(results):
    separator = "=" * 52
    section_separator = "-" * 52

    print(separator)
    print("RESUMEN DE LIBROS")
    print(separator)
    print(f"Total de libros:             {results['total_books']}")
    print(f"Registros validos:           {results['valid_books']}")
    print(f"Registros con errores:       {len(results['validation_errors'])}")
    print(f"Valor total del inventario:  {results['inventory_value']}")
    print(f"Titulos faltantes:           {results['missing_titles']}")

    print(section_separator)
    print("DISTRIBUCION POR GENERO")
    for genre, count in sorted(results["genres"].items()):
        print(f"  {genre}: {count}")

    print(section_separator)
    print("DISTRIBUCION POR STATUS")
    for status, count in sorted(results["statuses"].items()):
        print(f"  {status}: {count}")

    print(section_separator)
    print("ERRORES DE VALIDACION")
    if results["validation_errors"]:
        for error in results["validation_errors"]:
            reasons = "; ".join(error["motivos"])
            print(f"  Fila {error['fila']}: {reasons}")
    else:
        print("  Sin errores")
    print(separator)


def write_results_csv(results, csv_file):
    writer = csv.writer(csv_file)
    writer.writerow(["seccion", "elemento", "valor"])
    writer.writerows(
        [
            ["resumen", "total_libros", results["total_books"]],
            ["resumen", "registros_validos", results["valid_books"]],
            ["resumen", "registros_con_errores", len(results["validation_errors"])],
            ["resumen", "valor_total_inventario", results["inventory_value"]],
            ["resumen", "titulos_faltantes", results["missing_titles"]],
        ]
    )
    for genre, count in sorted(results["genres"].items()):
        writer.writerow(["genero", genre, count])
    for status, count in sorted(results["statuses"].items()):
        writer.writerow(["status", status, count])
    for error in results["validation_errors"]:
        writer.writerow(
            ["error_validacion", f"fila_{error['fila']}", "; ".join(error["motivos"])]
        )


def export_results(results, output_path):
    with open(output_path, mode="w", newline="", encoding="utf-8") as csv_file:
        write_results_csv(results, csv_file)


def main():
    parser = argparse.ArgumentParser(description="Lee un archivo CSV de libros.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("books.csv"),
        help="ruta del CSV (por defecto: books.csv junto a este script)",
    )
    args = parser.parse_args()

    try:
        results = analyze_books(args.csv_path)
    except FileNotFoundError:
        parser.error(f"no se encontro el archivo: {args.csv_path}")

    answer = input("exportar resultados a CSV?[S/N] ").strip().casefold()
    if answer == "s":
        output_path = Path(__file__).with_name("results.csv")
        export_results(results, output_path)
        print(f"Resultados exportados a: {output_path}")


if __name__ == "__main__":
    main()
