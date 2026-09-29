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


def analyze_books(csv_path):
    with open(csv_path, mode="r", newline="", encoding="utf-8") as csv_file:
        books = list(csv.DictReader(csv_file))

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

    print(f"Total de libros: {len(books)}")
    print(f"Registros validos: {len(valid_books)}")
    print(f"Registros con errores: {len(validation_errors)}")
    if validation_errors:
        print("Errores de validacion:")
        for error in validation_errors:
            print(f"  Fila {error['fila']}: {'; '.join(error['motivos'])}")
    print(f"Valor total del inventario: {inventory_value:.2f}")
    print(f"Titulos faltantes: {missing_titles}")
    print("Distribucion por genero:")
    for genre, count in sorted(genres.items()):
        print(f"  {genre}: {count}")
    print("Distribucion por status:")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")


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
        analyze_books(args.csv_path)
    except FileNotFoundError:
        parser.error(f"no se encontro el archivo: {args.csv_path}")


if __name__ == "__main__":
    main()
