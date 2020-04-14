import csv

TICKET_NUMBER = "Ticket # Full 13 digits please! )"
AIRLINE = "Airline"
TICKET_VALUE = "Ticket Value "
AIRLINE_PENALTY = "Airline Penalty"
TICKET_DATE_OF_ISSUE = "Ticket DOI"
AIRLINE_CONFIRMATION = "Airline Confirmation #"
NOTES = "Notes about booking"


def row_is_irrelevant(row):
    return (
        "YELLOW" in row[TICKET_NUMBER]
        or "ORANGE" in row[TICKET_NUMBER]
        or not any(v for k, v in row.items() if k)
    )


def main():
    with open("credits.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        result = []
        for row in reader:
            if row_is_irrelevant(row):
                continue
            else:
                result.append(
                    [
                        row[TICKET_NUMBER],
                        row[AIRLINE],
                        row[TICKET_VALUE],
                        row[AIRLINE_PENALTY],
                        row[TICKET_DATE_OF_ISSUE],
                        row[AIRLINE_CONFIRMATION],
                        row[NOTES],
                    ]
                )
    with open("extracted_fields.csv", "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(
            [
                "ticket_number",
                "airline",
                "ticket_value",
                "airline_penalty",
                "date_of_issue",
                "airline_confirmation",
                "notes",
            ]
        )
        for row in result:
            csv_writer.writerow(row)


if __name__ == "__main__":
    main()
