import genre_tree

song_file = 'data/song_file.csv'
genre_tree = genre_tree.create_genre_tree(song_file)

# needs the exact spelling in genre_tree, not case-sensitive
genre = input("Enter the genre you want (enter the exact genre or sub-genre)")

while True:
    if not genre_tree.find(genre.lower()):
        print("Genre is not in genre tree, try again")
        genre = input("Enter the genre you want (enter the exact genre or sub-genre)")
    else:
        break

# needs to be either 'yes' or 'no', not case-sensitive
bool_viral_song = input("Do you like viral songs? (enter yes or no)")

while True:
    if bool_viral_song.lower() != 'yes' and bool_viral_song != 'no':
        print("Invalid response, try again")
        bool_viral_song = input("Do you like viral songs? (enter yes or no)")
    else:
        break

# a float between [1, 10], inclusive
energy_level = input("Enter your energy level from 1 - 10")

while True:
    if float(energy_level) > 10 or float(energy_level) < 1:
        print("Invalid energy level, please enter a number between 1 and 10")
        energy_level = input("Enter your energy level from 1 - 10")
    else:
        break

print('Data: ')
print(genre)
print(bool_viral_song)
print(energy_level)

