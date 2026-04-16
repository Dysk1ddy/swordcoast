from dnd_game.game import TextDnDGame


if __name__ == "__main__":
    try:
        TextDnDGame().run()
    except KeyboardInterrupt:
        print("\nInput interrupted. Exiting cleanly.")
