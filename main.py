"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This is the main entry point for Playlistify. It allows the user to choose
between the Graphical User Interface (GUI) or the Console version.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
import sys
import gui
import console_version


def main() -> None:
    """Prompt the user for their preferred interface and launch the app."""
    print("==========================================")
    print("Welcome to Playlistify!")
    print("==========================================")
    print("How would you like to explore your music?")
    print("  [1] App Version (Graphical Interface)")
    print("  [2] Console Version (Text-based Interface)")
    print("  [q] Quit")

    choice = input("\nSelection: ").strip().lower()

    if choice == '1':
        print("\nLaunching GUI... Please wait.")
        gui.run_gui()
    elif choice == '2':
        print("\nLaunching Console Interface...\n")
        console_version.run_console()
    elif choice == 'q':
        print("Goodbye!")
        sys.exit()
    else:
        print("\nInvalid choice. Please enter 1, 2, or q.")
        main()


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['gui', 'console_version', 'sys'],
        'allowed-io': ['main'],
    })

    main()
