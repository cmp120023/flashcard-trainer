# Modular CS & Cyber-Physical Systems Flashcard Trainer

A lightweight, dark-mode Python desktop flashcard and **"Predict the Exact Output"** code-drill trainer built with `tkinter`, pre-loaded with **46 modular JSON decks (768 cards)** spanning Associate-level Computer Programming and Bachelor-level Cyber-Physical Software Engineering (BS-CS-CPSE).

## Features
- **Typed Active-Recall Input:** Requires typing exact answers or code outputs directly into the GUI before revealing explanations.
- **Modular Deck Architecture:** Automatically scans `decks/*.json` at startup or when clicking **Reload Decks**—drop in new JSON files anytime without touching Python code.
- **Progress Tracking & Archiving:** Tracks mastered card IDs locally in `mastered_cards.json` and lets you archive completed decks to `decks/mastered_archive/`.
- **Zero External Dependencies:** Runs on standard Python 3 (`tkinter`, `json`, `os`).

## Curriculum Coverage (46 Decks / 768 Cards)
- **Foundations & AAT Coursework:** C#, ASP.NET Core MVC & Web API, EF Core, T-SQL & LINQ, Java OOP, Modern C++17/20, Data Structures & Algorithms, SOLID/UML, Git CLI, and multi-language unit testing (`xUnit`, `pytest`, `GoogleTest`, `JUnit 5`, `Jest`).
- **Code-Output Gauntlets (v1–v7):** Multi-language edge-case output prediction drills across C, C++, C#, Python, Java, and JavaScript.
- **Cyber-Physical & Embedded Systems:** Bare-Metal C99/C11, ARM Cortex-M registers & startup/linker scripts, FreeRTOS/Zephyr, Embedded Linux (U-Boot, Yocto, Device Trees, `PREEMPT_RT`), Embedded Rust (`#![no_std]`, Type-State, Embassy), DSP/PID/Kalman filters, CAN/ROS 2/Motor FOC, Industrial PLC/OPC UA, KiCad/PCB debug, and Embedded Security/MISRA C++:2023/HIL testing.

## Quick Start (Windows)
1. Double-click **`Launch_Flashcards.bat`** (or run `python flashcards_gui.py` in your terminal).
2. Select a deck from the dropdown menu (or study across all active decks).
3. Type your answer in the input box and press **Enter** or click **Check Answer**.

## Adding Custom Decks
Place any `.json` file inside `decks/` following this schema and click **Reload Decks**:

```json
{
  "deck_name": "Custom Deck Title",
  "cards": [
    {
      "id": "unique_card_id",
      "category": "Topic",
      "type": "flashcard",
      "prompt": "Question text",
      "code": "Optional code snippet",
      "answer": "Canonical answer",
      "accepted_answers": ["Optional valid alias"],
      "explanation": "Concise technical explanation"
    }
  ]
}
```

## License
This project is for **educational and non-commercial use only**:
- **Software Code (`*.py`, `*.bat`):** [PolyForm Noncommercial License 1.0.0](https://polyformproject.org)
- **Flashcard Decks (`decks/*.json`):** [CC BY-NC 4.0](https://creativecommons.org)
