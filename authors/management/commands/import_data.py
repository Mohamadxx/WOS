import csv
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from authors.models import Author, Publication


def parse_bibliographic_file(file_path):
    """
    Parse the custom bibliographic file format into structured data.
    Each record is a dictionary.
    """
    publications = []
    record = {}

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            # Parse fields based on prefixes
            if line.startswith("TI"):
                record["title"] = line[3:].strip()
            elif line.startswith("DI"):
                record["doi"] = line[3:].strip()
            elif line.startswith("AU"):
                authors = record.get("authors", [])
                authors.append(line[3:].strip())
                record["authors"] = authors
            elif line.startswith("SO"):
                record["source"] = line[3:].strip()
            elif line.startswith("PY"):
                record["publication_date"] = line[3:].strip()
            elif line.startswith("VL"):
                record["volume"] = line[3:].strip()
            elif line.startswith("IS"):
                record["issue"] = line[3:].strip()
            elif line.startswith("BP"):
                record["pages"] = record.get("pages", "") + line[3:].strip()
            elif line.startswith("EP"):
                record["pages"] += f"-{line[3:].strip()}"
            elif line.startswith("ER"):
                # End of record: save and reset
                publications.append(record)
                record = {}

    return publications


class Command(BaseCommand):
    help = "Import data from CSV and text files into the database"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file containing publication data')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        if not os.path.exists(file_path):
            self.stderr.write(f"Error: File not found: {file_path}")
            return

        self.import_authors()
        self.import_publications(file_path)

    def generate_unique_slug(self, base_slug, model):
        """
        Generate a unique slug by appending a number if the slug already exists.
        """
        slug = base_slug
        counter = 1
        while model.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def import_authors(self):
        authors_file = 'data/author_h_index.csv'

        if not os.path.exists(authors_file):
            self.stderr.write(f"Error: File not found: {authors_file}")
            return

        with open(authors_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not row.get('name') or not row.get('h_index') or len(row['name'].strip()) == 0:
                    self.stdout.write(self.style.WARNING(f"Skipping row with missing data: {row}"))
                    continue

                base_slug = slugify(row['name'])
                unique_slug = self.generate_unique_slug(base_slug, Author)

                author, created = Author.objects.get_or_create(
                    name=row['name'].strip(),
                    defaults={
                        'slug': unique_slug,
                        'h_index': int(row['h_index']) if row['h_index'].isdigit() else 0,
                    },
                )

                if not created:
                    if row.get('h_index') and row['h_index'].isdigit():
                        author.h_index = int(row['h_index'])
                    author.save()

                if created:
                    self.stdout.write(f"Created new author: {author.name}")
                else:
                    self.stdout.write(f"Author already exists: {author.name}")

        self.stdout.write(self.style.SUCCESS('Successfully imported authors'))

    def import_publications(self, file_path):
        """
        Import parsed publication data into the database.
        """
        records = parse_bibliographic_file(file_path)

        for record in records:
            doi = record.get("doi")
            if not record.get("title"):
                self.stdout.write(self.style.ERROR("Skipping publication without a title."))
                continue

            fields = {
                "title": record.get("title"),
                "source": record.get("source"),
                "publication_date": record.get("publication_date"),
                "volume": record.get("volume"),
                "issue": record.get("issue"),
                "pages": record.get("pages"),
                "doi": doi,
            }

            try:
                # Update or create the publication
                publication_obj, created = Publication.objects.update_or_create(
                    doi=doi, defaults=fields
                )

                if "authors" in record:
                    author_objects = []
                    for author_name in record["authors"]:
                        author_slug = slugify(author_name)
                        author, _ = Author.objects.get_or_create(
                            name=author_name, defaults={"slug": author_slug}
                        )
                        author_objects.append(author)
                    publication_obj.authors.set(author_objects)

                if created:
                    self.stdout.write(f"Created new publication: {fields['title']}")
                else:
                    self.stdout.write(f"Updated existing publication: {fields['title']}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing publication: {e}"))

        self.stdout.write(self.style.SUCCESS("Successfully imported publications"))
