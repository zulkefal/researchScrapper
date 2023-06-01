import tkinter as tk
from tkinter import ttk
import time
import pandas as pd
import requests
import csv
import re
from bs4 import BeautifulSoup

# Create a GUI window
window = tk.Tk()
window.title("Research Scraper")  # Set the title of the window
window.geometry("1000x600")  # Set the size of the window
window.configure(bg="#f0f0f0")  # Set background color

# Define custom fonts
title_font = ("Helvetica", 16, "bold")
label_font = ("Helvetica", 12)
button_font = ("Helvetica", 12, "bold")

# Function to handle button click event
def acm_scrap_data():
    # Get user input from GUI elements
    query = query_entry.get()
    pages = int(pages_combobox.get())

    # Check if query is empty
    if not query:
        result_label.config(text="Please insert a query.", fg="red")
        return

    # Replace spaces with "+" in the query
    query = query.replace(" ", "+")

    # Create a list to store data
    results = []

    # Loop through each page and scrape data
    for page in range(1, pages + 1):
        url = f"https://dl.acm.org/action/doSearch?AllField={query}&pageNumber={page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        for entry in soup.find_all("div", attrs={"class": "issue-item__content"}):
            try:
                title_element = entry.find('h5', attrs={'class': 'issue-item__title'})
                title = title_element.text.replace('[PDF]', '')

                # Scrape the paper link
                paper_link = "https://dl.acm.org" + title_element.find('a')['href']

                author_elements = entry.find('ul', attrs={'class': 'rlist--inline'}).find_all('a')
                authors = [author.span.text.strip() for author in author_elements]
                author_links = [f"https://dl.acm.org{author['href']}" for author in author_elements]
                author_link = ', '.join(author_links)

                abst = entry.find('div', attrs={'class': 'issue-item__abstract'}).text.replace('\n', '')
                cite = entry.find('span', attrs={'class': 'citation'}).text
                years = entry.find('span', attrs={'class': 'dot-separator'}).text.split(',')[0].split(' ')[1]

                results.append({"Title": title, "Abstract": abst, "Citation": cite, "Year": years,
                                "Authors": authors, "Paper Link": paper_link, "Author Links": author_link})
            except Exception as e:
                print(f"An exception occurred: {e}")

        time.sleep(3)  # Wait before making the next request

    # Create a DataFrame from the list of data
    df = pd.DataFrame(results)

    # Save the DataFrame to a CSV file
    csv_filename = f"{query}.csv"
    df.to_csv(csv_filename, index=False)

    result_label.config(text=f"Scraped data saved to {csv_filename}.", fg="green")

    # Clear existing data from the treeview
    tree.delete(*tree.get_children())

    # Load the CSV file into the treeview
    df = pd.read_csv(csv_filename)
    for _, row in df.iterrows():
        tree.insert('', 'end', values=row.tolist())
def google_scrape_data():
    query = query_entry_gs.get()
    num_pages = int(pages_combobox_gs.get())

    # Check if query is empty
    if not query:
        result_label_gs.config(text="Please insert a query.", fg="red")
        return

    # Replace spaces with "+" in the query
    query = query.replace(" ", "+")

    # Initialize the list of results
    all_results = []

    # Set up the URL for the search term
    url = f"https://scholar.google.com/scholar?q={query}"
    # Make the request to Google Scholar and get the HTML response
    response = requests.get(url)
    html = response.text

    # Use BeautifulSoup to parse the HTML response
    soup = BeautifulSoup(html, 'html.parser')

    # Find all the titles and authors of the search results on the first page
    results = soup.find_all('div', {'class': 'gs_ri'})

    # Add the first page of results to the all_results list
    all_results.extend(results)

    # Find the URL of the "Next" page, if it exists
    next_url = soup.find('a', {'class': 'gs_ico gs_ico_nav_next'})
    while next_url and len(all_results) // 100 < num_pages:
        # Make the request to the next page and get the HTML response
        next_url = "https://scholar.google.com" + next_url['href']
        response = requests.get(next_url)
        html = response.text
        # Use BeautifulSoup to parse the HTML response
        soup = BeautifulSoup(html, 'html.parser')
        # Find all the titles and authors of the search results on this page
        results = soup.find_all('div', {'class': 'gs_ri'})
        # Add the results to the all_results list
        all_results.extend(results)
        # Find the URL of the next page, if it exists
        next_url = soup.find('a', {'class': 'gs_ico gs_ico_nav_next'})
        time.sleep(20)

    # Display the scraped data in the treeview
    for result in all_results:
        title = result.find('a').text
        authors_tag = result.find('div', {'class': 'gs_a'}).find_all('a')
        authors_a = ', '.join([tag.text for tag in authors_tag])
        authors_links = ', '.join([f"https://scholar.google.com{tag['href']}" for tag in authors_tag])

        target_tag = result.find('div', {'class': 'gs_fl'})
        cited_by_tag = target_tag.find('a', {'href': re.compile(r'cites=\d+')})
        if cited_by_tag is not None:
            cited_by_text = cited_by_tag.string
            cited_by_num = re.findall(r'\d+', cited_by_text)[0]
        else:
            cited_by_num = '0'

        # Extract the URL of the paper, if available
        result_tag = result.find('h3', {'class': 'gs_rt'})
        title_tag = result_tag.find('a')
        title = title_tag.text
        paper_link = title_tag['href']

        if title is not None and authors_a is not None:
            author_links_list = authors_links.split(', ')
            # Insert the data into the treeview
            tree_gs.insert("", "end", values=(title, authors_a, cited_by_num, paper_link) + tuple(author_links_list[:3]))
        else:
            result_label_gs.config(text="An error occurred.", fg="red")

    # Save the scraped data as a CSV file
    filename = query + ".csv"
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Title", "Authors", "Citation", "Paper Link", "Author1 Link", "Author2 Link", "Author3 Link"])
        for result in all_results:
            title = result.find('a').text
            authors_tag = result.find('div', {'class': 'gs_a'}).find_all('a')
            authors_a = ', '.join([tag.text for tag in authors_tag])
            authors_links = ', '.join([f"https://scholar.google.com{tag['href']}" for tag in authors_tag])

            target_tag = result.find('div', {'class': 'gs_fl'})
            cited_by_tag = target_tag.find('a', {'href': re.compile(r'cites=\d+')})
            if cited_by_tag is not None:
                cited_by_text = cited_by_tag.string
                cited_by_num = re.findall(r'\d+', cited_by_text)[0]
            else:
                cited_by_num = '0'

            # Extract the URL of the paper, if available
            result_tag = result.find('h3', {'class': 'gs_rt'})
            title_tag = result_tag.find('a')
            title = title_tag.text
            paper_link = title_tag['href']

            if title is not None and authors_a is not None:
                author_links_list = authors_links.split(', ')
                # Write the data to the CSV file
                writer.writerow([title, authors_a, cited_by_num, paper_link] + author_links_list[:3])
            else:
                result_label_gs.config(text="An error occurred.", fg="red")

    result_label_gs.config(text="Google Scholar Scraping completed.", fg="green")


# Create a notebook widget for multiple tabs
notebook = ttk.Notebook(window)
notebook.pack(fill='both', expand=True)

# Create the main tab for scraping data
main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="ACM Scraper")

# Configure columns and rows to expand for the main tab
main_tab.columnconfigure(0, weight=1)
main_tab.columnconfigure(1, weight=1)
main_tab.rowconfigure(0, weight=1)
main_tab.rowconfigure(1, weight=1)
main_tab.rowconfigure(2, weight=1)
main_tab.rowconfigure(3, weight=1)
main_tab.rowconfigure(4, weight=1)
main_tab.rowconfigure(5, weight=1)

# Create GUI elements for the main tab
query_label = tk.Label(main_tab, text="Enter your query:", font=label_font, bg="#f0f0f0")
query_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
query_entry = tk.Entry(main_tab, font=label_font)
query_entry.grid(row=0, column=1, sticky="we", padx=10, pady=10)

pages_label = tk.Label(main_tab, text="Enter the number of pages to scrape:", font=label_font, bg="#f0f0f0")
pages_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)
pages_combobox = ttk.Combobox(main_tab, values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], width=10, font=label_font)
pages_combobox.current(0)
pages_combobox.grid(row=1, column=1, sticky="we", padx=10, pady=10)

scrape_button = tk.Button(main_tab, text="Scrape Data", command=acm_scrap_data, font=button_font, bg="#4caf50", fg="white")
scrape_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

result_label = tk.Label(main_tab, text="", font=label_font, bg="#f0f0f0")
result_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

# Create a treeview widget with horizontal and vertical scrollbars
tree_frame = ttk.Frame(main_tab)
tree_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
tree_scroll = ttk.Scrollbar(tree_frame)
tree_scroll.pack(side='right', fill='y')
tree_scroll_x = ttk.Scrollbar(main_tab, orient='horizontal')
tree_scroll_x.grid(row=5, column=0, columnspan=2, sticky='we')
tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, xscrollcommand=tree_scroll_x.set)
tree.pack(fill='both', expand=True)
tree_scroll.config(command=tree.yview)
tree_scroll_x.config(command=tree.xview)

# Define columns for the treeview
tree["columns"] = ("Title", "Abstract", "Citation", "Year", "Authors", "Paper Link", "Author Links")

# Format column headers
tree.column("#0", width=0, stretch="no")
tree.column("Title", width=200)
tree.column("Abstract", width=200)
tree.column("Citation", width=60)
tree.column("Year", width=70)
tree.column("Authors", width=200)
tree.column("Paper Link", width=200)
tree.column("Author Links", width=200)

tree.heading("Title", text="Title")
tree.heading("Abstract", text="Abstract")
tree.heading("Citation", text="Citation")
tree.heading("Year", text="Year")
tree.heading("Authors", text="Authors")
tree.heading("Paper Link", text="Paper Link")
tree.heading("Author Links", text="Author Links")


google_scholar_tab = ttk.Frame(notebook)
notebook.add(google_scholar_tab, text="Google Scholar Scraper")

# Create a new tab for About Us
about_us_tab = ttk.Frame(notebook)
notebook.add(about_us_tab, text="About Us")

# Create a label with information about the program
about_label = tk.Label(
    about_us_tab,
    text="ResearchScraper is an application designed to facilitate the collection and extraction of research data from various sources.\n\nDeveloped by Muhammad Asim, Zulkefal, Muhammad Saadullah, and Abdul Moiz.",
    font=label_font,
    bg="#f0f0f0",
    wraplength=700  # Set the desired wrap length for the label
)


about_label.pack(padx=10, pady=10)

# Configure columns and rows to expand for the About Us tab
about_us_tab.columnconfigure(0, weight=1)
about_us_tab.rowconfigure(0, weight=1)

# Configure columns and rows to expand for the Google Scholar Scraper tab

google_scholar_tab.columnconfigure(0, weight=1)
google_scholar_tab.columnconfigure(1, weight=1)
google_scholar_tab.rowconfigure(0, weight=1)
google_scholar_tab.rowconfigure(1, weight=1)
google_scholar_tab.rowconfigure(2, weight=1)
google_scholar_tab.rowconfigure(3, weight=1)
google_scholar_tab.rowconfigure(4, weight=1)
google_scholar_tab.rowconfigure(5, weight=1)

############################
query_label_gs = tk.Label(google_scholar_tab, text="Enter your query:", font=label_font, bg="#f0f0f0")
query_label_gs.grid(row=0, column=0, sticky="w", padx=10, pady=10)
query_entry_gs = tk.Entry(google_scholar_tab, font=label_font)
query_entry_gs.grid(row=0, column=1, sticky="we", padx=10, pady=10)

pages_label_gs = tk.Label(google_scholar_tab, text="Enter the number of pages to scrape:", font=label_font, bg="#f0f0f0")
pages_label_gs.grid(row=1, column=0, sticky="w", padx=10, pady=10)
pages_combobox_gs = ttk.Combobox(google_scholar_tab, values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], width=10, font=label_font)
pages_combobox_gs.current(0)
pages_combobox_gs.grid(row=1, column=1, sticky="we", padx=10, pady=10)


scrape_button_gs = tk.Button(google_scholar_tab, text="Scrape Data", command=google_scrape_data, font=button_font, bg="#4caf50", fg="white")
scrape_button_gs.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

result_label_gs = tk.Label(google_scholar_tab, text="", font=label_font, bg="#f0f0f0")
result_label_gs.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

# Create a treeview widget with horizontal and vertical scrollbars
tree_frame_gs = ttk.Frame(google_scholar_tab)
tree_frame_gs.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Create a horizontal scrollbar
tree_scroll_x_gs = ttk.Scrollbar(tree_frame_gs, orient='horizontal')
tree_scroll_x_gs.pack(side='bottom', fill='x')

# Create a vertical scrollbar
tree_scroll_gs = ttk.Scrollbar(tree_frame_gs)
tree_scroll_gs.pack(side='right', fill='y')

# Create the Treeview widget
tree_gs = ttk.Treeview(
    tree_frame_gs,
    yscrollcommand=tree_scroll_gs.set,
    xscrollcommand=tree_scroll_x_gs.set
)
tree_gs.pack(fill='both', expand=True)

# Configure the scrollbars
tree_scroll_gs.config(command=tree_gs.yview)
tree_scroll_x_gs.config(command=tree_gs.xview)

# Define columns for the treeview
tree_gs["columns"] = ("Title", "Authors", "Citation", "Paper Link", "Author1 Link", "Author2 Link", "Author3 Link")

# Format column headers
tree_gs.column("#0", width=0, stretch="no")
tree_gs.column("Title", width=200)
tree_gs.column("Authors", width=200)
tree_gs.column("Citation", width=60)
tree_gs.column("Paper Link", width=200)
tree_gs.column("Author1 Link", width=200)
tree_gs.column("Author2 Link", width=200)
tree_gs.column("Author3 Link", width=200)

tree_gs.heading("Title", text="Title")
tree_gs.heading("Authors", text="Authors")
tree_gs.heading("Citation", text="Citation")
tree_gs.heading("Paper Link", text="Paper Link")
tree_gs.heading("Author1 Link", text="Author1 Link")
tree_gs.heading("Author2 Link", text="Author2 Link")
tree_gs.heading("Author3 Link", text="Author3 Link")



# Add the Google Scholar Scraper tab to the notebook
notebook.add(google_scholar_tab, text="Google Scholar Scraper")



# Center the window on the screen
window.update_idletasks()
width = window.winfo_width()
height = window.winfo_height()
x = (window.winfo_screenwidth() // 2) - (width // 2)
y = (window.winfo_screenheight() // 2) - (height // 2)
window.geometry(f"{width}x{height}+{x}+{y}")

# Start the GUI event loop
window.mainloop()
