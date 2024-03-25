import io
import pandas as pd


def convert_html_table_to_csv(html_string: str):
    # Wrap the HTML string in a StringIO object
    html_string_io = io.StringIO(html_string)

    # Read the HTML table from the StringIO object into a DataFrame
    df = pd.read_html(html_string_io)[0]

    # Create a StringIO object to capture the CSV output
    csv_output = io.StringIO()

    # Write the DataFrame to the StringIO object as CSV
    df.to_csv(csv_output, index=False)

    # Get the CSV-formatted string from the StringIO object
    csv_string = csv_output.getvalue()

    # Possibliy save it or something, idk yet

    print(csv_string)
