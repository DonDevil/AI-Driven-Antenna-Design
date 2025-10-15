import tkinter as tk
from tkinter import messagebox, scrolledtext
import json
import os
import re
json_path = r"cst_interface\database\material_library.json"

def macro_to_json(macro_text):
    material_dict = {}
    current_material = None
    for line in macro_text.splitlines():
        line = line.strip()
        if line.startswith('.Name '):
            # Get material name
            current_material = line.split(' ', 1)[1].replace('"', '').strip()
            material_dict[current_material] = {'name': current_material}
        elif line.startswith('.') and current_material:
            # Extract flag and value(s)
            parts = line[1:].split(' ', 1)
            flag = parts[0].strip().lower()
            if len(parts) > 1:
                val_part = parts[1].strip()
                # Find all quoted argument parts (handles multiple)
                values = re.findall(r'"([^"]*)"', val_part)
                # If only one, store as string, if multiple, store as list
                if not values:
                    value = ""
                elif len(values) == 1:
                    value = values[0]
                else:
                    value = values
                material_dict[current_material][flag] = value
            else:
                # no value, store empty string
                material_dict[current_material][flag] = ""
    return material_dict

def add_material():
    macro_text = text_box.get("1.0", tk.END).strip()
    if not macro_text:
        messagebox.showwarning("Input needed", "Please paste the macro text in the box before adding.")
        return
    try:
        new_material_json = macro_to_json(macro_text)
        # Load existing JSON
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                try:
                    existing_materials = json.load(f)
                except json.JSONDecodeError:
                    existing_materials = {}
        else:
            existing_materials = {}
        # Update dictionary
        existing_materials.update(new_material_json)
        # Save back
        with open(json_path, 'w') as f:
            json.dump(existing_materials, f, indent=2)
        messagebox.showinfo("Success", f"Material(s) added successfully:\n{', '.join(new_material_json.keys())}")
        text_box.delete("1.0", tk.END)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add material:\n{e}")

# Create main window
root = tk.Tk()
root.title("CST Material Library Updater")

label = tk.Label(root, text="Paste CST Material Macro Text below:")
label.pack(padx=10, pady=(10, 0))

text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
text_box.pack(padx=10, pady=10)

add_button = tk.Button(root, text="Add to Library", command=add_material)
add_button.pack(pady=(0, 10))

root.mainloop()
