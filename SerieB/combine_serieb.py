import os
from PIL import Image
from itertools import permutations

# Parametri
WIDTH, HEIGHT = 348, 182
CENTER_SIZE = 70

# Prendi tutti i file png (escludi serieb.png e image.png)
all_files = [f for f in os.listdir('.') if f.endswith('.png')]
team_files = [f for f in all_files if f not in ['serieb.png', 'image.png']]

# Carica l'immagine centrale
center_img = Image.open('serieb.png').convert('RGBA')
center_img = center_img.resize((CENTER_SIZE, CENTER_SIZE), Image.LANCZOS)

for team1, team2 in permutations(team_files, 2):
    if team1 == team2:
        continue  # Salta i doppioni (es. lazio-lazio)
    outname = f"{os.path.splitext(team1)[0]}_vs_{os.path.splitext(team2)[0]}.png"
    if os.path.exists(outname):
        continue  # Evita di sovrascrivere se già creato (opzionale)

    # Carica e ridimensiona le immagini delle squadre
    img1 = Image.open(team1).convert('RGBA').resize((WIDTH // 2, HEIGHT), Image.LANCZOS)
    img2 = Image.open(team2).convert('RGBA').resize((WIDTH // 2, HEIGHT), Image.LANCZOS)

    # Crea immagine finale vuota
    combined = Image.new('RGBA', (WIDTH, HEIGHT))

    # Incolla le due squadre
    combined.paste(img1, (0, 0), img1)
    combined.paste(img2, (WIDTH // 2, 0), img2)

    # Incolla il logo Serie A al centro
    x_center = (WIDTH - CENTER_SIZE) // 2
    y_center = (HEIGHT - CENTER_SIZE) // 2
    combined.paste(center_img, (x_center, y_center), center_img)

    # Salva con compressione PNG
    combined.save(outname, optimize=True)
    print(f"Creato: {outname}")
