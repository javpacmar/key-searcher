from tkinter import *
from tkinter import messagebox
import os
import shutil
from urllib.request import urlopen, Request
import urllib.parse
from bs4 import BeautifulSoup

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, NUMERIC, ID

dirindex = "indexdir"


def get_data():
    response = messagebox.askyesno(
        title="Confirm", message="Do you want to get the data? This may take a while")
    if response:
        save_data()


def save_data():
    '''Get data from different game shop websites and save it into a whoosh index'''
    # Create the index
    schm = Schema(title=TEXT(stored=True), price=NUMERIC(
        stored=True, numtype=float), url=ID(stored=True), source=TEXT(stored=True, phrase=False))

    # Delete the index if it exists
    if os.path.exists(dirindex):
        shutil.rmtree(dirindex)
    os.mkdir(dirindex)

    # Create the index
    ix = create_in(dirindex, schema=schm)
    writer = ix.writer()
    i = 0

    # Get the game name from an input box with a tkinter window
    v = Toplevel()
    v.title("Get Data")
    v.geometry("300x100")
    Label(v, text="Game name:").pack()
    game_name = Entry(v)
    game_name.pack()
    Button(v, text="Get Data", command=v.quit).pack()
    v.mainloop()

    # Get the keys from the different game shops
    keys_list = get_keys(urllib.parse.quote(game_name.get()))

    # Save the data into the index
    for key in keys_list:
        writer.add_document(
            title=key[0], price=key[1], url=key[2], source=key[3])
        i += 1
    writer.commit()
    messagebox.showinfo(title="Success", message="{} keys saved".format(i))

    l = get_keys(game_name)
    for title, price, url, source in l:
        writer.add_document(title=str(title), price=float(
            price), url=str(url), source=str(source))
        i += 1
        print("Added: " + title)
    writer.commit()
    messagebox.showinfo(
        title="Info", message="Data saved with {} games".format(i))


def get_keys(game):
    keys_list = []
    keys_list.extend(get_keys_from_steam(game))
    keys_list.extend(get_keys_from_ig(game))
    return keys_list


def get_keys_from_ig(game):
    '''Get the keys from Instant Gaming'''
    URL = "https://www.instant-gaming.com/en/search/?q=" + game
    req = Request(
        url=URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    f = urlopen(req)
    s = BeautifulSoup(f, "html.parser")
    games_item = s.find_all("div", class_="item")
    key_list = []
    for game_item in games_item:
        print(game_item)
        title = game_item.find("span", class_="title").text.strip()
        price = game_item.find(
            "div", class_="price").text.strip().replace("€", "")
        url = game_item.find("a")['href']
        key_list.append((title, price, url, "Instant Gaming"))
    return key_list


def get_keys_from_steam(game):
    '''Get the keys from Steam'''
    URL = "https://store.steampowered.com/search/?term=" + game
    f = urlopen(URL)
    s = BeautifulSoup(f, "html.parser")
    games_link = s.find_all(
        "a", class_=["search_result_row", "ds_collapse_flag"])
    key_list = []
    for game_link in games_link:
        title = game_link.find("span", class_="title").text.strip()
        # Check if price is discounted
        if game_link.find("div", class_="col search_price discounted responsive_secondrow"):
            price = game_link.find(
                "div", class_="col search_price discounted responsive_secondrow").text.split("€")[1].strip()
        elif game_link.find("div", class_="col search_price responsive_secondrow"):
            price = game_link.find(
                "div", class_="col search_price responsive_secondrow").text.strip()
        else:
            price = 0
        price = price.replace(",", ".").replace("€", "").lower()
        if price in ("free", "free to play", "gratuito", ""):
            price = 0
        url = game_link["href"]
        key_list.append((title, price, url, "Steam"))
    return key_list


def list_data(result):
    '''List the result in a listbox in a new window'''
    v = Toplevel()
    v.title("List Data")
    v.geometry("600x400")
    lb = Listbox(v)
    lb.pack(side=LEFT, fill=BOTH, expand=1)
    sc = Scrollbar(v, command=lb.yview)
    sc.pack(side=RIGHT, fill=Y)
    sc.config(command=lb.yview)
    for r in result:
        lb.insert(
            END, "{} - {} - {}".format(r['title'], r['price'], r['source']))


def list_all_data():
    '''List all the data from the index'''
    ix = open_dir(dirindex)
    with ix.searcher() as searcher:
        result = searcher.documents()
        list_data(result)


def main_window():
    w = Tk()
    w.title("Key Seacher")

    menu = Menu(w)

    # Data menu
    data_menu = Menu(menu, tearoff=0)
    data_menu.add_command(label="Get Data", command=get_data)
    data_menu.add_command(label="List Data", command=list_all_data)
    data_menu.add_separator()
    data_menu.add_command(label="Exit", command=w.quit)

    menu.add_cascade(label="Data", menu=data_menu)

    w.config(menu=menu)
    w.mainloop()


if __name__ == "__main__":
    main_window()
